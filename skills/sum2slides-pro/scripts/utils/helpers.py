"""Common helper functions for Sum2Slides Pro."""

import json
import os
from pathlib import Path
from datetime import datetime


def safe_json(obj):
    return json.loads(json.dumps(obj, default=str))


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def time_str(seconds):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def detect_speakers(text):
    """Detect unique speakers from a text pattern like 'Name: message'."""
    import re
    speakers = set()
    for line in text.split('\n'):
        line = line.strip()
        m = re.match(r'^(\*{0,2})([\w\u4e00-\u9fff\s]+?):\s', line)
        if m:
            speakers.add(m.group(2).strip().strip('*'))
    return sorted(speakers)
