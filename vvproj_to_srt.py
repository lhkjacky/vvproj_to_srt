import json
import sys
from pathlib import Path


def seconds_to_srt_time(sec):
    hours = int(sec // 3600)
    minutes = int((sec % 3600) // 60)
    seconds = int(sec % 60)
    milliseconds = int((sec - int(sec)) * 1000)

    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def get_item_duration(audio_item):
    total = 0.0

    query = audio_item.get("query", {})
    accent_phrases = query.get("accentPhrases", [])

    for phrase in accent_phrases:
        for mora in phrase.get("moras", []):
            total += mora.get("consonantLength") or 0
            total += mora.get("vowelLength") or 0

        # pause mora
        pause = phrase.get("pauseMora")
        if pause:
            total += pause.get("vowelLength") or 0

    # add post silence
    total += query.get("postPhonemeLength", 0)

    return total


def convert(vvproj_path):
    with open(vvproj_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    audio_items = (
        data.get("talk", {})
        .get("audioItems", {})
    )

    output_lines = []
    current_time = 0.0
    index = 1

    for key, item in audio_items.items():
        text = item.get("text", "").strip()
        if not text:
            continue

        duration = get_item_duration(item)

        start = current_time
        end = current_time + duration

        output_lines.append(str(index))
        output_lines.append(
            f"{seconds_to_srt_time(start)} --> {seconds_to_srt_time(end)}"
        )
        output_lines.append(text)
        output_lines.append("")

        current_time = end
        index += 1

    return "\n".join(output_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python vvproj_to_srt.py file.vvproj")
        return

    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".srt")

    srt_text = convert(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_text)

    print(f"✅ SRT created: {output_path}")


if __name__ == "__main__":
    main()
