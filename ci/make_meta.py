#!/usr/bin/env python3
"""Creates missing Unity .meta files under Assets/ for files written outside the Editor.

Without a committed .meta, every CI run would import the file with a new random GUID.
The formats copy what Unity 6000.3 itself wrote into this repo (see any existing
.cs.meta, folder .meta, or .asmdef.meta). Only types whose format has been observed
here are handled; anything else is reported and left for Unity to create.

    python3 ci/make_meta.py            # create missing metas
    python3 ci/make_meta.py --check    # exit 1 if any are missing (no writes)
"""
import os
import sys
import uuid

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Assets")

FOLDER = ("fileFormatVersion: 2\nguid: {g}\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {{}}\n"
          "  userData: \n  assetBundleName: \n  assetBundleVariant: \n")
SCRIPT = "fileFormatVersion: 2\nguid: {g}"
ASMDEF = ("fileFormatVersion: 2\nguid: {g}\nAssemblyDefinitionImporter:\n  externalObjects: {{}}\n"
          "  userData: \n  assetBundleName: \n  assetBundleVariant: \n")
TEMPLATES = {".cs": SCRIPT, ".asmdef": ASMDEF}


def main():
    check = "--check" in sys.argv
    missing, unknown = [], []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and not d.endswith("~")]
        entries = [(d, True) for d in dirnames] + [(f, False) for f in filenames if not f.endswith(".meta")]
        for name, is_dir in entries:
            path = os.path.join(dirpath, name)
            if os.path.exists(path + ".meta"):
                continue
            template = FOLDER if is_dir else TEMPLATES.get(os.path.splitext(name)[1])
            rel = os.path.relpath(path, os.path.join(ROOT, ".."))
            if template is None:
                unknown.append(rel)
                continue
            missing.append(rel)
            if not check:
                with open(path + ".meta", "w", newline="\n") as f:
                    f.write(template.format(g=uuid.uuid4().hex))
    for rel in missing:
        print(("MISSING " if check else "created ") + rel + ".meta")
    for rel in unknown:
        print("unknown type, left for Unity: " + rel)
    return 1 if (check and missing) else 0


if __name__ == "__main__":
    sys.exit(main())
