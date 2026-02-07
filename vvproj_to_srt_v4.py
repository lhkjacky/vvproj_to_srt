import json
import sys
from pathlib import Path


def srt_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def get_item_duration(item):
    query = item.get("query")
    if not query:
        return 0.0

    speed = query.get("speedScale", 1.0)
    pre = query.get("prePhonemeLength", 0.0)
    post = query.get("postPhonemeLength", 0.0)
    pause_scale = query.get("pauseLengthScale", 1.0)

    total = pre

    for phrase in query.get("accentPhrases", []):
        for mora in phrase.get("moras", []):
            total += mora.get("consonantLength") or 0
            total += mora.get("vowelLength") or 0

        pause = phrase.get("pauseMora")
        if pause:
            total += (pause.get("vowelLength") or 0) * pause_scale

    total += post

    if speed != 0:
        total /= speed

    return total


def convert(vvproj_path, timing_correction):
    data = json.loads(Path(vvproj_path).read_text(encoding="utf-8"))

    items = data.get("talk", {}).get("audioItems", {})

    if not items:
        print("❌ No audioItems found")
        return ""

    current = 0.0
    idx = 1
    out = []

    for item in items.values():
        text = item.get("text", "").strip()
        if not text:
            continue

        dur = get_item_duration(item)
        if dur <= 0:
            continue

        start = current * timing_correction
        end = (current + dur) * timing_correction

        out.append(str(idx))
        out.append(f"{srt_time(start)} --> {srt_time(end)}")
        out.append(text)
        out.append("")

        current += dur
        idx += 1

    print(f"Processed {idx - 1} subtitle lines")
    print(f"Calculated raw duration: {current:.2f} seconds")
    print(f"After timing correction: {current * timing_correction:.2f} seconds")

    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("python vvproj_to_srt.py file.vvproj [timing_correction]")
        return

    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".srt")

    # Default = no correction
    timing_correction = 0.9955 
    
    if len(sys.argv) >= 3:
        try:
            timing_correction = float(sys.argv[2])
        except ValueError:
            print("Invalid timing correction value. Using 1.0")

    print(f"Using timing correction: {timing_correction}")

    srt_text = convert(input_path, timing_correction)

    if not srt_text:
        print("❌ No subtitles generated")
        return

    output_path.write_text(srt_text, encoding="utf-8")

    print(f"✅ SRT created: {output_path}")


if __name__ == "__main__":
    main()

