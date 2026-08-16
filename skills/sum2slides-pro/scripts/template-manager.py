#!/usr/bin/env python3
"""Sum2Slides Pro — Template Manager"""

import argparse
import json
import sys
from pathlib import Path


def list_templates():
    tmpl_dir = Path(__file__).parent.parent / "templates"
    templates = []
    for f in sorted(tmpl_dir.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
            templates.append({
                "name": data.get("name", f.stem),
                "description": data.get("description", ""),
                "layouts": list(data.get("layouts", {}).keys()),
                "colors": list(data.get("style", {}).get("colors", {}).keys())
            })
    return templates


def show_template(name):
    tmpl_dir = Path(__file__).parent.parent / "templates"
    tmpl_file = tmpl_dir / f"{name}.json"
    if not tmpl_file.exists():
        return {"error": f"Template '{name}' not found"}
    with open(tmpl_file) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Sum2Slides Pro — Template Manager")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--show", help="Show template details")
    args = parser.parse_args()

    if args.list:
        templates = list_templates()
        print(f"Available templates ({len(templates)}):")
        for t in templates:
            layouts = ", ".join(t["layouts"])
            print(f"  {t['name']:15s} {t['description']:40s} [{layouts}]")

    if args.show:
        data = show_template(args.show)
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
