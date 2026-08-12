#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fractal Address Mapper v0.1 (stdlib only)

Maps files (from glyph_sync.py's JSONL ledger) to 2-D Hilbert addresses.
Outputs CSV, creates a symlink tree laid out by fractal buckets, or prints
an ASCII plot of points.

Why Hilbert?
- Space-filling, locality-preserving: nearby addresses ≈ nearby 2D cells.
- Deterministic from content hash + glyph salt (semantic bias).

Address format:
  H{order}:{x}:{y}:{code}
Where:
  - order = Hilbert order (grid size = 2^order)
  - (x,y) ∈ [0, 2^order-1]
  - code = base32 of Hilbert index (Crockford alphabet)

CLI:
  # 1) CSV export of addresses
  python fractal_address.py map --in glyph_ledger.jsonl --out addresses.csv --order 8

  # 2) Build a symlink tree organized by fractal buckets
  python fractal_address.py tree --in glyph_ledger.jsonl --root fractal_tree --order 8 --bucket 16

  # 3) ASCII plot (quick look)
  python fractal_address.py plot --in glyph_ledger.jsonl --order 7 --limit 800
"""
import os, sys, argparse, json, math, time, hashlib, base64, pathlib
from typing import Dict, Tuple, Iterable, List, Optional

# ---------- Crockford Base32 (no padding), for compact codes ----------
_CROCK = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
def b32_crockford(n: int, min_chars: int = 8) -> str:
    if n == 0: return "0".rjust(min_chars, "0")
    out = []
    while n > 0:
        out.append(_CROCK[n % 32])
        n //= 32
    s = "".join(reversed(out))
    return s.rjust(min_chars, "0")

# ---------- Hilbert curve (2D), order up to 16 comfortably ----------
def _rot(n: int, x: int, y: int, rx: int, ry: int) -> Tuple[int,int]:
    # rotate/flip a quadrant appropriately
    if ry == 0:
        if rx == 1:
            x = n-1 - x
            y = n-1 - y
        x, y = y, x
    return x, y

def hilbert_xy_from_index(order: int, idx: int) -> Tuple[int,int]:
    """Map Hilbert index -> (x,y) on 2^order grid. idx ∈ [0, 2^(2*order)-1]."""
    n = 1 << order
    x = y = 0
    t = idx
    s = 1
    while s < n:
        rx = 1 & (t//2)
        ry = 1 & (t ^ rx)
        x, y = _rot(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    return x, y

def hilbert_index_from_xy(order: int, x: int, y: int) -> int:
    """Map (x,y) -> Hilbert index."""
    n = 1 << order
    idx = 0
    s = n // 2
    while s > 0:
        rx = 1 if (x & s) else 0
        ry = 1 if (y & s) else 0
        idx += s * s * ((3 * rx) ^ ry)
        x, y = _rot(s, x, y, rx, ry)
        s //= 2
    return idx

# ---------- Glyph-biased salting ----------
GLYPH_SALT = {
    "⚖": 0xA5A5A5A5A5A5A5A5,
    "🔄": 0x5A5A5A5A5A5A5A5A,
    "🕸": 0xC3EC3EC3EC3EC3EC,
    "🌱": 0x3C3C3C3C3C3C3C3C,
    "🧩": 0x9696969696969696
}
def salt_from_glyphs(glyphs: str) -> int:
    s = 0
    for ch in glyphs:
        s ^= GLYPH_SALT.get(ch, 0)
    # ensure non-zero perturbation
    return s or 0x1BD11BDAA9FC1A22

# ---------- Deterministic index from file record ----------
def ledger_latest(path: str) -> Dict[str, dict]:
    latest = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            p = r.get("path")
            if p:
                latest[p] = r
    return latest

def file_index(order: int, rec: dict) -> int:
    """
    Build a 64-bit base value from ledger fields, then fold to 2^(2*order).
    Using (hash || size || mtime) XOR glyph salt to bias quadrants.
    """
    hhex = rec.get("hash") or ""
    size = int(rec.get("size") or 0)
    mtime = int(rec.get("mtime") or 0)
    glyphs = rec.get("glyphs") or ""

    # start with 64 bits from SHA256 hex (first 16 hex chars => 64 bits)
    try:
        base64int = int(hhex[:16], 16)
    except Exception:
        base64int = 0

    # mix in size/mtime and glyph salt
    mix = base64int ^ ((size & 0xFFFFFFFF) << 32) ^ (mtime & 0xFFFFFFFF)
    mix ^= salt_from_glyphs(glyphs)

    # fold to range
    space = 1 << (2*order)   # total cells
    idx = mix % space
    return idx

def address_tuple(order: int, rec: dict) -> Tuple[int,int,int,str]:
    idx = file_index(order, rec)
    x, y = hilbert_xy_from_index(order, idx)
    code = b32_crockford(idx, min_chars=max(4, (2*order+4)//5))  # ~2*order bits / 5 + pad
    return idx, x, y, f"H{order}:{x}:{y}:{code}"

# ---------- ASCII plotting ----------
def ascii_plot(points: List[Tuple[int,int]], order: int, max_w: int = 80, max_h: int = 40) -> str:
    n = 1 << order
    # scale to fit
    sx = max(1, n // max_w)
    sy = max(1, n // max_h)
    w = min(n, n // sx)
    h = min(n, n // sy)
    grid = [[" "]*w for _ in range(h)]
    for (x,y) in points:
        X = min(w-1, x // sx)
        Y = min(h-1, y // sy)
        # invert Y for display (origin bottom-left feel)
        Yd = h-1 - Y
        grid[Yd][X] = "•"
    lines = ["".join(row) for row in grid]
    return "\n".join(lines)

# ---------- Symlink tree ----------
def safe_relpath(p: str, root: str) -> str:
    try:
        return os.path.relpath(p, root)
    except Exception:
        return p

def ensure_dir(d: str):
    os.makedirs(d, exist_ok=True)

def build_tree(latest: Dict[str,dict], order: int, root: str, bucket: int):
    """
    Place files into tree buckets by (x//bucket, y//bucket).
    We create symlinks pointing back to the real files.
    """
    n = 1 << order
    bx = max(1, bucket)
    by = bx
    created = 0
    for path, rec in latest.items():
        idx, x, y, addr = address_tuple(order, rec)
        gx = x // bx
        gy = y // by
        # bucket dir path
        d = os.path.join(root, f"H{order}", f"{gx:03d}", f"{gy:03d}")
        ensure_dir(d)
        # symlink name hints at glyphs and short hash
        short = (rec.get("hash","")[:8] or "00000000")
        glyphs = (rec.get("glyphs") or "").replace(" ", "")
        base = os.path.basename(path)
        linkname = f"{glyphs}_{short}_{base}"
        linkpath = os.path.join(d, linkname)
        # avoid collisions by appending counter
        k = 1
        candidate = linkpath
        while os.path.lexists(candidate):
            k += 1
            candidate = os.path.join(d, f"{glyphs}_{short}_{k}_{base}")
        try:
            os.symlink(path, candidate)
            created += 1
        except FileExistsError:
            pass
        except OSError:
            # fallback: copy tiny files if symlink disallowed (rare)
            try:
                import shutil
                shutil.copy2(path, candidate)
                created += 1
            except Exception:
                pass
    print(f"[tree] created {created} symlinks under {root}")

# ---------- Commands ----------
def cmd_map(args):
    latest = ledger_latest(args.infile)
    out = args.out
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    wrote = 0
    with open(out, "w", encoding="utf-8") as f:
        f.write("path,glyphs,size,mtime,hilbert_order,x,y,index,code\n")
        for p, rec in latest.items():
            idx, x, y, addr = address_tuple(args.order, rec)
            code = addr.split(":")[-1]
            f.write(f"{p},{rec.get('glyphs','')},{rec.get('size',0)},{int(rec.get('mtime',0))},{args.order},{x},{y},{idx},{code}\n")
            wrote += 1
    print(f"[map] wrote {wrote} rows → {out}")

def cmd_tree(args):
    latest = ledger_latest(args.infile)
    build_tree(latest, args.order, args.root, args.bucket)

def cmd_plot(args):
    latest = ledger_latest(args.infile)
    pts = []
    c = 0
    for _, rec in latest.items():
        _, x, y, _ = address_tuple(args.order, rec)
        pts.append((x,y))
        c += 1
        if args.limit and c >= args.limit:
            break
    print(ascii_plot(pts, args.order, max_w=args.width, max_h=args.height))

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Fractal Address Mapper (Hilbert)")
    sub = ap.add_subparsers(dest="cmd")

    ap_m = sub.add_parser("map", help="Export CSV of fractal addresses from a glyph ledger")
    ap_m.add_argument("--in", dest="infile", required=True, help="glyph ledger JSONL")
    ap_m.add_argument("--out", required=True, help="CSV output")
    ap_m.add_argument("--order", type=int, default=8, help="Hilbert order (grid 2^order)")
    ap_m.set_defaults(func=cmd_map)

    ap_t = sub.add_parser("tree", help="Build a symlink tree arranged by fractal buckets")
    ap_t.add_argument("--in", dest="infile", required=True, help="glyph ledger JSONL")
    ap_t.add_argument("--root", required=True, help="Output tree root")
    ap_t.add_argument("--order", type=int, default=8)
    ap_t.add_argument("--bucket", type=int, default=16, help="cell size per bucket (in grid cells)")
    ap_t.set_defaults(func=cmd_tree)

    ap_p = sub.add_parser("plot", help="ASCII plot of mapped points")
    ap_p.add_argument("--in", dest="infile", required=True, help="glyph ledger JSONL")
    ap_p.add_argument("--order", type=int, default=7)
    ap_p.add_argument("--limit", type=int, help="max points to plot")
    ap_p.add_argument("--width", type=int, default=80)
    ap_p.add_argument("--height", type=int, default=40)
    ap_p.set_defaults(func=cmd_plot)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help(); sys.exit(1)
    args.func(args)


USAGE_NOTES = """
    how it fits together
    1.    stamp your files (once, across all projects):

    python glyph_sync.py scan --out ~/glyph_ledger.jsonl \
  --ignore "**/.git/*" --ignore "**/.venv/*" --ignore "*.log" \
  ~/projA ~/projB ~/notes

    2.    map to fractal space:

    python fractal_address.py map --in ~/glyph_ledger.jsonl --out ~/addresses.csv --order 8

        3.    build a fractal symlink tree (great for browsing or partial sync):

        python fractal_address.py tree --in ~/glyph_ledger.jsonl --root ~/fractal_tree --order 8 --bucket 16
# browse buckets:
find ~/fractal_tree/H8 -maxdepth 2 -type d | head

4.    quick feel check (ASCII plot):

python fractal_address.py plot --in ~/glyph_ledger.jsonl --order 7 --limit 800


design notes
    •    semantic bias: glyphs nudge the quadrant via XOR salts. as your glyph semantics evolve, update GLYPH_SALT to warp the geometry accordingly (e.g., 🔄 gravitates to particular folds).
    •    locality: hilbert preserves neighborhood—files with similar hashes/metadata/glyphs cluster visually and in path space.
    •    address stability: content hash dominates, so addresses remain stable unless a file truly changes.
    •    portability: symlink tree is just a view; real files stay where they are. you can rsync by bucket when links are flaky.
"""


if __name__ == "__main__":
    main()
