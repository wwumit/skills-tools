#!/usr/bin/env python3
"""
Excel2Insights Pro — Full Analysis Pipeline

One-command pipeline: load → analyze → chart → dashboard.
Generates interactive HTML dashboard with all charts and insights.

Usage:
    python3 scripts/auto-pipeline.py --file data.csv
    python3 scripts/auto-pipeline.py --file data.csv --charts histogram,bar,heatmap,scatter
    python3 scripts/auto-pipeline.py --file data.csv --brand-json brand.json
"""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run_script(script_name, args_line):
    """Run a companion script via direct import (replaces subprocess)."""
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return None
    print(f"  → Running: {script_name} {' '.join(args_line.split()[:4])}...")
    old_argv = sys.argv.copy()
    try:
        mod_name = script_name.replace('.py', '')
        spec = importlib.util.spec_from_file_location(mod_name, script_path)
        mod = importlib.util.module_from_spec(spec)
        sys.argv = [str(script_path)] + args_line.split()
        spec.loader.exec_module(mod)
        if hasattr(mod, 'main'):
            mod.main()
        return 0
    except SystemExit as e:
        return e.code or 0
    except Exception as e:
        print(f"  ⚠️  Error in {script_name}: {e}")
        return 1
    finally:
        sys.argv = old_argv


def main():
    parser = argparse.ArgumentParser(description="Excel2Insights Pro — Full Analysis Pipeline")
    parser.add_argument("--file", required=True, help="Path to data file (CSV/XLSX/TSV)")
    parser.add_argument("--charts", default="histogram,bar,heatmap,scatter",
                        help="Comma-separated chart types")
    parser.add_argument("--charts-only", nargs="?", const="1", help="Skip analysis, generate from existing JSON")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--format", default="html", choices=["html", "markdown", "both"],
                        help="Report format")
    parser.add_argument("--brand-json", help="Brand configuration JSON file")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.file))[0]

    # Step 1: Load & Inspect
    print("\n📂 Step 1: Loading file...")
    rc = run_script("excel-reader.py", f"--file '{args.file}' --json")
    if rc != 0:
        print("⚠️  Reader returned non-zero. Continuing...")

    # Step 2: Statistical Analysis
    print("\n📊 Step 2: Analyzing data...")
    analysis_json = os.path.join(args.output, f"{base}_analysis.json")
    rc = run_script("data-analyzer.py",
                     f"--file '{args.file}' --output '{analysis_json}' --correlation --outliers")
    if rc != 0 and not os.path.exists(analysis_json):
        print("❌ Analysis failed")
        sys.exit(1)

    # Step 3: Generate interactive charts
    print("\n📈 Step 3: Generating interactive charts...")
    charts_dir = os.path.join(args.output, "charts")
    rc = run_script("chart-generator.py",
                     f"--file '{args.file}' --charts '{args.charts}' --output '{charts_dir}'")

    # Step 4: Generate dashboard
    print("\n🎨 Step 4: Generating dashboard...")
    dashboard_path = os.path.join(args.output, f"{base}_dashboard.html")
    brand_arg = f"--brand-json '{args.brand_json}'" if args.brand_json else ""
    rc = run_script("dashboard-generator.py",
                     f"--file '{args.file}' --analysis '{analysis_json}' "
                     f"--charts '{charts_dir}' --output '{dashboard_path}' {brand_arg}")

    # Step 5: Generate Markdown report (optional)
    if args.format in ("markdown", "both"):
        print("\n📝 Step 5: Generating Markdown report...")
        report_path = os.path.join(args.output, f"{base}_report.md")
        run_script("report-generator.py",
                    f"--file '{args.file}' --analysis '{analysis_json}' "
                    f"--charts '{charts_dir}' --output '{report_path}'")

    # Summary
    print("\n✅ Pipeline complete!")
    print(f"   📊 Interactive dashboard: {dashboard_path}")
    print(f"   📈 Charts: {charts_dir}/")
    if args.format in ("markdown", "both"):
        print(f"   📝 Report: {os.path.join(args.output, f'{base}_report.md')}")
    print(f"   📋 Analysis: {analysis_json}")
    print(f"\n   Open the dashboard in your browser to explore interactive charts.")

    if args.json:
        summary = {
            "dashboard": dashboard_path,
            "analysis": analysis_json,
            "charts_dir": charts_dir,
            "charts": args.charts,
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
