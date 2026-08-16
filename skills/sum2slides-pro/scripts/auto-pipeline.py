#!/usr/bin/env python3
"""Sum2Slides Pro — Auto Pipeline (secure version, no subprocess)"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def load_module(filepath, name):
    """Import a Python file as a module."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser(description="Sum2Slides Pro — Auto Pipeline")
    parser.add_argument("--input", required=True, help="Path to chat file")
    parser.add_argument("--format", choices=["auto", "text", "markdown", "json"],
                        default="auto", help="Input format")
    parser.add_argument("--template", default="meeting",
                        help="Template name (default: meeting)")
    parser.add_argument("--output", default="output/summary.pptx", help="Output PPTX")
    parser.add_argument("--brand-logo", help="Company logo image")
    parser.add_argument("--brand-color", help="Theme accent color (hex)")
    parser.add_argument("--max-slides", type=int, default=50, help="Max slides")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    out_dir = Path(args.output).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    step_dir = out_dir / "steps"
    step_dir.mkdir(exist_ok=True)

    # Load sub-modules
    chat_parser = load_module(script_dir / "chat-parser.py", "chat_parser")
    topic_extractor = load_module(script_dir / "topic-extractor.py", "topic_extractor")
    slide_builder = load_module(script_dir / "slide-builder.py", "slide_builder")

    print("=" * 55)
    print("  Sum2Slides Pro — Auto Pipeline")
    print("=" * 55)

    # Step 1: Parse
    print("\n[1/3] Parsing dialogue...")
    parsed_path = step_dir / "parsed.json"
    result = chat_parser.parse_file(args.input, args.format, "utf-8")
    if "error" in result:
        print(f"  FAILED: {result['error']}")
        sys.exit(1)
    parsed_path.parent.mkdir(parents=True, exist_ok=True)
    parsed_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  {result.get('total_messages', 0)} messages, "
          f"{result.get('speaker_count', 0)} speakers")

    # Step 2: Extract
    print("\n[2/3] Analyzing content...")
    outline_path = step_dir / "outline.json"
    outline = topic_extractor.analyze(str(parsed_path), 3, str(outline_path))
    m = outline.get("metadata", {})
    print(f"  Topics: {m.get('topics_found', 0)} | "
          f"Decisions: {m.get('decisions_found', 0)} | "
          f"Actions: {m.get('action_items_found', 0)} | "
          f"Consensus: {m.get('consensus_found', 0)} | "
          f"Divergence: {m.get('divergence_found', 0)}")

    # Step 3: Build slides
    print(f"\n[3/3] Generating PPTX ({args.template})...")
    with open(outline_path) as f:
        outline_data = json.load(f)

    output_path, slide_count = slide_builder.build(
        outline_data, args.template, args.output,
        args.brand_logo, args.brand_color, args.max_slides
    )

    print(f"\n{'=' * 55}")
    print(f"  Pipeline Complete!")
    print(f"  Output: {output_path}")
    print(f"  Slides: {slide_count}")
    print(f"{'=' * 55}")

    summary = {
        "status": "success",
        "input": args.input,
        "messages": result.get("total_messages", 0),
        "speakers": result.get("speaker_count", 0),
        "topics": m.get("topics_found", 0),
        "decisions": m.get("decisions_found", 0),
        "actions": m.get("action_items_found", 0),
        "consensus": m.get("consensus_found", 0),
        "divergence": m.get("divergence_found", 0),
        "slides": slide_count,
        "output": args.output,
        "template": args.template
    }
    print(f"\n{json.dumps(summary, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
