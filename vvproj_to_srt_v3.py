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


def convert(vvproj):
    data = json.loads(Path(vvproj).read_text(encoding="utf-8"))

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

        start = current
        end = current + dur

        out.append(str(idx))
        out.append(f"{srt_time(start)} --> {srt_time(end)}")
        out.append(text)
        out.append("")

        current = end
        idx += 1

    print(f"Processed {idx-1} subtitle lines")
    print(f"Total duration approx {current:.2f} seconds")

    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("Usage: python vvproj_to_srt.py file.vvproj")
        return

    inp = Path(sys.argv[1])
    outp = inp.with_suffix(".srt")

    srt = convert(inp)

    if not srt:
        print("❌ No subtitles generated")
        return

    outp.write_text(srt, encoding="utf-8")

    print("✅ SRT created:", outp)


if __name__ == "__main__":
    main()
