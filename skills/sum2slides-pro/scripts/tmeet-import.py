#!/usr/bin/env python3
"""
Sum2Slides Pro — Tencent Meeting Import

Converts Tencent Meeting AI纪要/转写 data into Sum2Slides input format.
Call this AFTER fetching meeting data via the 腾讯会议 Skill.

Usage:
  python3 scripts/tmeet-import.py --transcript transcript.json --output chat.txt
  python3 scripts/tmeet-import.py --summary ai_summary.md --output chat.txt
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_transcript(data):
    """Convert Tencent Meeting transcript JSON to Sum2Slides chat format."""
    messages = []
    if isinstance(data, dict):
        segments = data.get("transcript") or data.get("segments") or data.get("sentences") or []
        meeting_title = data.get("subject") or data.get("title") or "Meeting Discussion"
    elif isinstance(data, list):
        segments = data
        meeting_title = "Meeting Discussion"
    else:
        return None, None

    for seg in segments:
        speaker = seg.get("speaker") or seg.get("user_name") or seg.get("nick_name") or "Speaker"
        text = seg.get("text") or seg.get("content") or seg.get("sentence") or ""
        if text.strip():
            messages.append(f"{speaker.strip()}: {text.strip()}")
    return messages, meeting_title


def parse_ai_summary(text):
    """Convert Tencent Meeting AI纪要 markdown text to Sum2Slides chat format."""
    lines = text.strip().split('\n')
    messages = []
    current_speaker = None
    meeting_title = "Meeting Summary"

    for line in lines:
        m = re.match(r'^#\s+(.+)', line)
        if m:
            meeting_title = m.group(1).strip()
            break

    for line in lines:
        line = line.strip()
        if not line:
            continue
        sm = re.match(r'^\*{0,2}([\w\u4e00-\u9fff\s]+?)\*{0,2}:?\s+(.*)', line)
        if sm:
            speaker = sm.group(1).strip().strip('*').strip()
            content = sm.group(2).strip()
            if content and not content.startswith('#'):
                current_speaker = speaker
                messages.append(f"{speaker}: {content}")
        elif current_speaker and re.match(r'^[-*]\s', line):
            text = re.sub(r'^[-*\s]+', '', line).strip()
            if text:
                messages.append(f"{current_speaker}: {text}")
    return messages, meeting_title


def main():
    parser = argparse.ArgumentParser(
        description="Sum2Slides Pro — Tencent Meeting Import")
    parser.add_argument("--transcript", help="Tencent Meeting transcript JSON file")
    parser.add_argument("--summary", help="Tencent Meeting AI纪要 markdown file")
    parser.add_argument("--output", default="output/tmeet-chat.txt",
                        help="Output chat file path")
    args = parser.parse_args()

    if not args.transcript and not args.summary:
        print("[ERROR] Provide --transcript or --summary", file=sys.stderr)
        sys.exit(1)

    messages = []
    title = "Meeting Discussion"

    if args.transcript:
        with open(args.transcript, encoding="utf-8") as f:
            data = json.load(f)
        msgs, t = parse_transcript(data)
        messages.extend(msgs)
        title = t or title

    if args.summary:
        with open(args.summary, encoding="utf-8") as f:
            text = f.read()
        msgs, t = parse_ai_summary(text)
        messages.extend(msgs)
        title = t or title

    if not messages:
        print("[ERROR] No messages extracted", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write("\n".join(messages))
        f.write("\n")

    print(f"✅ Imported {len(messages)} messages from Tencent Meeting")
    print(f"   Title: {title}")
    print(f"   Output: {args.output}")


if __name__ == "__main__":
    main()
