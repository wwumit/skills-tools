#!/usr/bin/env python3
"""
Sum2Slides Pro — Chat Parser
Parse multi-speaker dialogue from various input formats into structured JSON.
Supports: plain text, Markdown, JSON array.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_plain_text(text):
    """Parse plain text with speaker labels like 'Name: message'."""
    messages = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Pattern: "Speaker: message"
        m = re.match(r'^(\*{0,2})([\w\u4e00-\u9fff\s\-]+?):\s*(.*)$', line, re.DOTALL)
        if m:
            speaker = m.group(2).strip().strip('*')
            content = m.group(3).strip()
            if content:
                messages.append({"speaker": speaker, "text": content})
        else:
            # Treat as continuation of previous message or system note
            if messages:
                messages[-1]["text"] += "\n" + line
            else:
                messages.append({"speaker": "System", "text": line})
    return messages


def parse_markdown(text):
    """Parse Markdown with ## headings as topic markers and **Speaker:** labels."""
    messages = []
    current_topic = None
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Topic heading
        hm = re.match(r'^##+\s+(.*)', line)
        if hm:
            current_topic = hm.group(1).strip()
            messages.append({
                "type": "topic_marker",
                "topic": current_topic,
                "text": f"--- Topic: {current_topic} ---"
            })
            continue
        # Speaker
        sm = re.match(r'^\*{0,2}([\w\u4e00-\u9fff\s\-]+?)\*{0,2}:\s*(.*)', line)
        if sm:
            speaker = sm.group(1).strip().strip('*')
            content = sm.group(2).strip()
            if content:
                entry = {"speaker": speaker, "text": content}
                if current_topic:
                    entry["topic"] = current_topic
                messages.append(entry)
        else:
            if messages and "speaker" in messages[-1]:
                messages[-1]["text"] += "\n" + line
            else:
                messages.append({"speaker": "System", "text": line, "topic": current_topic})
    return messages


def parse_json(text):
    """Parse structured JSON array of {speaker, text, timestamp?}."""
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "messages" in data:
            return data["messages"]
    except json.JSONDecodeError:
        pass
    return None


def parse_file(filepath, fmt="auto", encoding="utf-8"):
    filepath = Path(filepath)
    if not filepath.exists():
        return {"error": f"File not found: {filepath}"}

    text = filepath.read_text(encoding=encoding)

    if fmt == "auto":
        # Try JSON first, then Markdown, then plain text
        parsed = parse_json(text)
        if parsed:
            fmt = "json"
        elif "##" in text[:500]:
            fmt = "markdown"
        else:
            fmt = "text"

    if fmt == "json":
        messages = parse_json(text)
        if messages is None:
            return {"error": "Invalid JSON format"}
    elif fmt == "markdown":
        messages = parse_markdown(text)
    else:
        messages = parse_plain_text(text)

    # Extract metadata
    speakers = list(dict.fromkeys(m.get("speaker", "") for m in messages if "speaker" in m))
    speakers = [s for s in speakers if s]

    return {
        "format": fmt,
        "total_messages": len([m for m in messages if "speaker" in m]),
        "speakers": speakers,
        "speaker_count": len(speakers),
        "messages": messages,
        "raw_text": text
    }


def main():
    parser = argparse.ArgumentParser(description="Sum2Slides Pro — Chat Parser")
    parser.add_argument("--input", required=True, help="Path to chat/dialogue file")
    parser.add_argument("--format", choices=["auto", "text", "markdown", "json"],
                        default="auto", help="Input format")
    parser.add_argument("--encoding", default="utf-8", help="File encoding")
    parser.add_argument("--output", help="Output JSON path")
    args = parser.parse_args()

    result = parse_file(args.input, args.format, args.encoding)
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Parsed: {result.get('total_messages', 0)} messages, "
              f"{result.get('speaker_count', 0)} speakers")
        print(f"Output: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
