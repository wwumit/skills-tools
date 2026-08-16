#!/usr/bin/env python3
"""
Excel2Insights Pro — Interactive Chart Generator (Plotly)

Generates interactive Plotly charts from structured data.
Supports: histogram, boxplot, bar, line, pie, heatmap, scatter, pairplot.
Outputs interactive HTML files (self-contained, zoomable, hoverable).

Usage:
    python3 scripts/chart-generator.py --file data.csv --charts histogram,bar,correlation
"""

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def load_data(filepath, sheet=None, encoding="utf-8"):
    """Load data from CSV/XLSX/TSV file."""
    ext = Path(filepath).suffix.lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(filepath, sheet_name=sheet or 0)
    elif ext == ".tsv":
        df = pd.read_csv(filepath, sep="\t", encoding=encoding)
    else:
        df = pd.read_csv(filepath, encoding=encoding)
    return df


def _detect_column_types(df):
    """Detect numeric, categorical, and datetime columns."""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = []
    for col in df.columns:
        try:
            pd.to_datetime(df[col])
            date_cols.append(col)
        except (ValueError, TypeError):
            pass
    return num_cols, cat_cols, date_cols


def _filter_columns(df, columns, needed):
    """Filter columns: if specified, intersect; otherwise use needed."""
    if columns:
        return [c for c in (columns if isinstance(columns, list) else columns.split(",")) if c in df.columns and c in needed]
    return needed


def _histogram(df, columns, out_dir):
    """Interactive histogram for numeric columns."""
    files = []
    num_cols, _, _ = _detect_column_types(df)
    cols = _filter_columns(df, columns, num_cols)
    for col in cols[:6]:  # limit to 6
        fig = px.histogram(df, x=col, title=f"Distribution of {col}",
                           marginal="box", nbins=30)
        fig.update_layout(template="plotly_white", height=400)
        path = os.path.join(out_dir, f"histogram_{col}.html")
        fig.write_html(path, include_plotlyjs="cdn", full_html=False)
        files.append(path)
    return files


def _boxplot(df, columns, out_dir):
    """Interactive boxplot for numeric columns."""
    files = []
    num_cols, cat_cols, _ = _detect_column_types(df)
    cols = _filter_columns(df, columns, num_cols)
    for col in cols[:8]:
        fig = px.box(df, y=col, title=f"Boxplot of {col}", points="outliers")
        fig.update_layout(template="plotly_white", height=400)
        path = os.path.join(out_dir, f"boxplot_{col}.html")
        fig.write_html(path, include_plotlyjs="cdn", full_html=False)
        files.append(path)
    return files


def _bar(df, columns, out_dir):
    """Interactive bar chart for categorical data."""
    files = []
    _, cat_cols, _ = _detect_column_types(df)
    cols = _filter_columns(df, columns, cat_cols)
    for col in cols[:6]:
        vc = df[col].value_counts().head(20).reset_index()
        vc.columns = [col, "count"]
        fig = px.bar(vc, x=col, y="count", title=f"Top Values in {col}",
                     text_auto=True, color="count", color_continuous_scale="Blues")
        fig.update_layout(template="plotly_white", height=400, xaxis_tickangle=-45)
        path = os.path.join(out_dir, f"bar_{col}.html")
        fig.write_html(path, include_plotlyjs="cdn", full_html=False)
        files.append(path)
    return files


def _line(df, columns, out_dir):
    """Interactive line chart for time-series data."""
    files = []
    num_cols, _, date_cols = _detect_column_types(df)
    date_col = date_cols[0] if date_cols else None
    if not date_col:
        return files
    cols = _filter_columns(df, columns, num_cols)
    for col in cols[:4]:
        fig = px.line(df, x=date_col, y=col, title=f"{col} Over Time",
                      markers=True)
        fig.update_layout(template="plotly_white", height=400)
        path = os.path.join(out_dir, f"line_{col}.html")
        fig.write_html(path, include_plotlyjs="cdn", full_html=False)
        files.append(path)
    return files


def _pie(df, columns, out_dir):
    """Interactive pie chart for categorical data."""
    files = []
    _, cat_cols, _ = _detect_column_types(df)
    cols = _filter_columns(df, columns, cat_cols)
    for col in cols[:4]:
        vc = df[col].value_counts().head(10)
        fig = px.pie(values=vc.values, names=vc.index, title=f"Proportion of {col}")
        fig.update_layout(template="plotly_white", height=400)
        path = os.path.join(out_dir, f"pie_{col}.html")
        fig.write_html(path, include_plotlyjs="cdn", full_html=False)
        files.append(path)
    return files


def _heatmap(df, columns, out_dir):
    """Interactive correlation heatmap for numeric columns."""
    num_cols, _, _ = _detect_column_types(df)
    cols = _filter_columns(df, columns, num_cols)
    if len(cols) < 2:
        return []
    corr = df[cols].corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                    title="Correlation Heatmap", aspect="auto",
                    zmin=-1, zmax=1)
    fig.update_layout(template="plotly_white", height=500)
    path = os.path.join(out_dir, "correlation_heatmap.html")
    fig.write_html(path, include_plotlyjs="cdn", full_html=False)
    return [path]


def _scatter(df, columns, out_dir):
    """Interactive scatter plot for numeric columns."""
    files = []
    num_cols, cat_cols, _ = _detect_column_types(df)
    cols = _filter_columns(df, columns, num_cols)
    if len(cols) < 2:
        return files
    color_col = cat_cols[0] if cat_cols else None
    for i in range(min(len(cols) - 1, 3)):
        fig = px.scatter(df, x=cols[i], y=cols[i + 1],
                         color=color_col, title=f"{cols[i]} vs {cols[i + 1]}",
                         hover_data=df.columns[:3].tolist(), opacity=0.7)
        fig.update_layout(template="plotly_white", height=450)
        path = os.path.join(out_dir, f"scatter_{cols[i]}_{cols[i + 1]}.html")
        fig.write_html(path, include_plotlyjs="cdn", full_html=False)
        files.append(path)
    return files


def _pairplot(df, columns, out_dir):
    """Interactive scatter matrix (pairplot) for numeric columns."""
    num_cols, cat_cols, _ = _detect_column_types(df)
    cols = _filter_columns(df, columns, num_cols)
    if len(cols) < 2 or len(cols) > 6:
        return []
    color_col = cat_cols[0] if cat_cols else None
    fig = px.scatter_matrix(df, dimensions=cols, color=color_col,
                            title="Scatter Matrix", height=600)
    fig.update_layout(template="plotly_white")
    path = os.path.join(out_dir, "pairplot.html")
    fig.write_html(path, include_plotlyjs="cdn", full_html=False)
    return [path]


CHART_FUNCTIONS = {
    "histogram": _histogram,
    "boxplot": _boxplot,
    "bar": _bar,
    "line": _line,
    "pie": _pie,
    "heatmap": _heatmap,
    "scatter": _scatter,
    "pairplot": _pairplot,
}


def generate_charts(df, chart_types, columns=None, output_dir="output/charts"):
    """Generate interactive Plotly charts from dataframe."""
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    for chart_type in chart_types:
        if chart_type in CHART_FUNCTIONS:
            files = CHART_FUNCTIONS[chart_type](df, columns, output_dir)
            results[chart_type] = files
    return results


def main():
    parser = argparse.ArgumentParser(description="Excel2Insights Pro — Interactive Chart Generator")
    parser.add_argument("--file", required=True, help="Path to data file")
    parser.add_argument("--encoding", default="utf-8")
    parser.add_argument("--charts", default="histogram,bar,correlation",
                        help="Comma-separated: histogram,boxplot,bar,line,pie,heatmap,scatter,pairplot")
    parser.add_argument("--columns", help="Comma-separated column filter")
    parser.add_argument("--output", default="output/charts", help="Output directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if not HAS_PLOTLY:
        print("❌ Plotly not installed. Run: pip install plotly")
        sys.exit(1)

    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)

    df = load_data(args.file, encoding=args.encoding)
    chart_types = [c.strip() for c in args.charts.split(",")]
    results = generate_charts(df, chart_types, columns=args.columns, output_dir=args.output)

    total = sum(len(v) for v in results.values())
    print(f"✅ Generated {total} interactive charts in {args.output}/")
    for chart_type, files in results.items():
        for f in files:
            print(f"   📊 {os.path.basename(f)}")

    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
