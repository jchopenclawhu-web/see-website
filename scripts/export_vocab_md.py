#!/usr/bin/env python3
"""
Export the website vocabulary JSON into one markdown file per level per semester.

Why: DeepTutor's knowledge bases ingest files (upload / github-source / web-source),
not Google Sheets. This script is the bridge:

    Sheets -> data/vocab_{current,archived}.json -> data/kb/{current,archived}/*.md

One markdown file per level per semester, in two directories:

    data/kb/current/<level>.md     current semester (2026 Fall)
    data/kb/archived/<level>.md    frozen prior semester (2025 Fall)

The two directories are separate on purpose. DeepTutor keys a github-source by
md5(repo:branch:path), so one KB can hold at most ONE source per path — a
second source needs a second path. Splitting current/archived into their own
directories lets a single KB take both, while keeping the archived semester out
of the default path.

Per-level files (rather than one big file) because DeepTutor grants knowledge
bases per user account. One KB per level, and a student gets cumulative grants
(BASIC + L1 + L2 for a Level 2 student), mirrors the level hierarchy the
existing esl-rag-chatbot already implements.

Usage:
  python3 scripts/export_vocab_md.py            # write data/kb/**/*.md
  python3 scripts/export_vocab_md.py --check    # verify files match the JSON
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "kb"
OUT_CURRENT = OUT / "current"
OUT_ARCHIVED = OUT / "archived"

LEVEL_KEYS = ["basic", "level1", "level2", "level3", "level4"]


def render(words, level, label):
    """One `## word` heading per entry so chunks break on the word boundary."""
    lines = [f"# Vocabulary — {level} ({label})", ""]
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
    """Return {relative_path: content} for every markdown file we publish."""
    out = {}
    for bucket, subdir, json_name, label_key in (
        ("current", OUT_CURRENT, "vocab_current.json", "current_label"),
        ("archived", OUT_ARCHIVED, "vocab_archived.json", "archived_label"),
    ):
        data = json.loads((DATA / json_name).read_text(encoding="utf-8"))
        label = data.get(label_key, "")
        for level in LEVEL_KEYS:
            name = f"vocab_{bucket}_{level}.md"
            out[f"{subdir.relative_to(ROOT)}/{name}"] = render(data.get(level, []), level, label)
    return out


def main():
    check = "--check" in sys.argv
    files = build()
    if check:
        bad = [rel for rel, body in files.items()
               if not (ROOT / rel).exists() or (ROOT / rel).read_text(encoding="utf-8") != body]
        if bad:
            print("STALE: " + ", ".join(bad))
            return 1
        print(f"OK: {len(files)} files match the JSON")
        return 0
    for rel, body in files.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        print(f"wrote {rel} ({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
