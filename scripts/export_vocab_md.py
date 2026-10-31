#!/usr/bin/env python3
"""
Export the website vocabulary JSON into one markdown file per level per semester.

Why: DeepTutor's knowledge bases ingest files (upload / github-source / web-source),
not Google Sheets. This script is the bridge: Sheets -> data/vocab_{current,archived}.json
-> data/kb/vocab_{current,archived}_{level}.md.

One markdown file per level per semester because DeepTutor chunks on document
boundaries and grants KBs per user account: a student at Level 2 should only
ever retrieve Level 2 material. The archived semester lives in the same
directory but under a distinct filename so it can be excluded from a KB by
glob, or given its own KB.

Usage:
  python3 scripts/export_vocab_md.py            # write data/kb/*.md
  python3 scripts/export_vocab_md.py --check    # verify files match the JSON
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "kb"

LEVEL_KEYS = ["basic", "level1", "level2", "level3", "level4"]

# DeepTutor KB filename convention.
SLUG = {"basic": "basic", "level1": "level1", "level2": "level2",
        "level3": "level3", "level4": "level4"}


def render(words, level, label):
    lines = [f"# Vocabulary \u2014 {level} ({label})", ""]
    for w in words:
        word = (w.get("word") or "").strip()
        if not word:
            continue
        lines.append(f"## {word}")
        for src, dst in (("chinese", "Chinese"),
                         ("example_1", "Example 1"), ("trans_1", "Translation 1"),
                         ("example_2", "Example 2"), ("trans_2", "Translation 2")):
            val = (w.get(src) or "").strip()
            if val:
                lines.append(f"- {dst}: {val}")
        lines.append("")
    return "\n".join(lines) + "\n"


def build():
    out = {}
    for bucket, json_name, label_key in (
        ("current", "vocab_current.json", "current_label"),
        ("archived", "vocab_archived.json", "archived_label"),
    ):
        data = json.loads((DATA / json_name).read_text(encoding="utf-8"))
        label = data.get(label_key, "")
        for level in LEVEL_KEYS:
            name = f"vocab_{bucket}_{SLUG[level]}.md"
            out[name] = render(data.get(level, []), level, label)
    return out


def main():
    check = "--check" in sys.argv
    files = build()
    if check:
        bad = []
        for name, body in files.items():
            p = OUT / name
            if not p.exists() or p.read_text(encoding="utf-8") != body:
                bad.append(name)
        if bad:
            print("STALE: " + ", ".join(bad))
            return 1
        print(f"OK: {len(files)} files match the JSON")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (OUT / name).write_text(body, encoding="utf-8")
        print(f"wrote {name} ({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
