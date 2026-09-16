#!/usr/bin/env python3
"""Verify every internal href/src in the built static site resolves to an existing file.

Usage:  python3 check_links.py [site_root]
Exit 0 when no bad links, 1 otherwise.
"""
import os, re, posixpath, sys

root = sys.argv[1] if len(sys.argv) > 1 else "."
os.chdir(root)

existing_files = set()
for dirpath, _, files in os.walk("."):
    for f in files:
        rel = posixpath.normpath(os.path.join(dirpath[2:] if dirpath.startswith("./") else dirpath, f))
        existing_files.add(rel)

def resolve(base_dir, ref):
    is_dir_ref = ref.endswith("/")
    parts = (base_dir.split("/") if base_dir else []) + ref.split("/")
    out = []
    for p in parts:
        if p in ("", ".", "/"):
            continue
        if p == "..":
            if out:
                out.pop()
        else:
            out.append(p)
    return "/".join(out), is_dir_ref

bad = set()
for dirpath, _, files in os.walk("."):
    base_dir = dirpath[2:] if dirpath.startswith("./") else (dirpath or "")
    for f in files:
        if not f.endswith(".html"):
            continue
        text = open(os.path.join(dirpath, f)).read()
        for mref in re.findall(r'(?:href|src)="([^"]+)"', text):
            if mref.startswith(("http", "#", "mailto", "data:")):
                continue
            mref = mref.split("?")[0].split("#")[0]
            if not mref:
                continue
            p, is_dir = resolve(base_dir, mref)
            if p == "":
                continue
            if is_dir:
                ok = os.path.exists(p + "/index.html") if p else True
            else:
                ok = p in existing_files
            if not ok:
                bad.add((mref, base_dir))

# external product links (should be 0 navigational links to builder/mev subdomains)
import subprocess
ext = subprocess.run(
    ["grep", "-rn", "builder\\.advalorem\\.io\\|mev\\.advalorem\\.io",
     "--include=*.html", ".", "-h"],
    capture_output=True, text=True).stdout
ext_links = [l for l in ext.splitlines() if 'href="https://builder.advalorem.io' in l or 'href="https://mev.advalorem.io' in l]

print(f"internal bad links: {len(bad)}")
for m, b in sorted(bad):
    print(f"  {m}  <=  {b}")
print(f"external builder/mev <a href> links: {len(ext_links)}")
for l in ext_links:
    print(f"  {l.strip()}")
sys.exit(1 if bad or ext_links else 0)
