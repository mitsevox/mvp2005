#!/usr/bin/env python3
"""Copy a file from a public decomp into this repo, byte for byte, with a one-line provenance note.

The note goes on the first line as a C comment; nothing else in the file changes (it is copied as
bytes, so backslashes and line endings survive). Each import is also listed in
config/<ver>/imported_units.tsv by hand (see CREDITS.md).

usage: import_upstream.py --root <upstream checkout> --repo emoose/re4 [--via doldecomp/dolsdk2004]
                          [--what "Nintendo Dolphin SDK 2004 Patch 1, os library"]
                          <upstream path> <our path> [<upstream path> <our path> ...]
"""
import argparse
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="the upstream checkout")
    ap.add_argument("--repo", required=True, help="upstream name, e.g. emoose/re4")
    ap.add_argument("--via", help="where the upstream took it from, e.g. doldecomp/dolsdk2004")
    ap.add_argument("--what", help="what the file is, e.g. 'Nintendo Dolphin SDK, os library'")
    ap.add_argument("--force", action="store_true", help="overwrite an existing file")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    if len(args.paths) % 2:
        sys.exit("paths come in pairs: <upstream path> <our path>")
    commit = subprocess.run(
        ["git", "-C", args.root, "rev-parse", "--short=8", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    for src, dst in zip(args.paths[0::2], args.paths[1::2]):
        data = open(os.path.join(args.root, src), "rb").read()
        note = f"Imported from {args.repo} @ {commit} ({src})"
        if args.via:
            note += f", based on {args.via}"
        if args.what:
            note += f". {args.what}"
        note += "."
        if "*/" in note:
            sys.exit(f"bad note: {note}")
        header = f"/* {note} */\n".encode()
        if os.path.exists(dst) and not args.force:
            sys.exit(f"{dst} exists (use --force)")
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        with open(dst, "wb") as f:
            f.write(header + data)
        print(f"{src} -> {dst}")


if __name__ == "__main__":
    main()
