#!/usr/bin/env python3
"""
JS & CSS Bundle Builder
=======================
Concatenates and minifies JS/CSS files into page-specific bundles.
Output goes to static/dist/js/ and static/dist/css/.

Usage:
    python build_bundles.py          # Build all bundles (production, minified)
    python build_bundles.py --dev    # Build without minification (faster)
    python build_bundles.py --clean  # Remove dist/ folder
"""

import hashlib
import shutil
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC = BASE_DIR / "static"
DIST_JS = STATIC / "dist" / "js"
DIST_CSS = STATIC / "dist" / "css"

# ─── JS Bundle Definitions ───────────────────────────────────────────────
# Each bundle is (output_name, [list of source files relative to static/])

JS_BUNDLES = [
    # ── Core: loaded on every dashboard page ──
    (
        "core.min.js",
        [
            "js/core/field-classifier.js",
            "js/core/api.js",
            "js/core/session-keepalive.js",
            "js/core/toast.js",
            "js/core/confirm.js",
            "js/core/modal.js",
            "js/core/utils.js",
            "js/core/sanitizer.js",
            "js/core/confirmation-code.js",
            "js/core/download-manager.js",
            "js/init.js",
        ],
    ),
]

# ─── CSS Bundle Definitions ──────────────────────────────────────────────

CSS_BUNDLES = [
    # ── Core CSS (loaded on every dashboard page) ──
    (
        "core.min.css",
        [
            "css/fonts.css",
            "css/common.css",
            "css/global-search.css",
        ],
    ),
    # ── Website Admin CSS ──
    (
        "wa.min.css",
        [
            "css/wa-layout.css",
            "css/wa-components.css",
            "css/wa-table.css",
            "css/wa-forms.css",
            "css/wa-modals.css",
        ],
    ),
]


def _content_hash(data: bytes) -> str:
    """Return first 8 chars of MD5 for cache verification."""
    return hashlib.md5(data).hexdigest()[:8]


def concat_files(file_list: list[str], base: Path) -> str:
    """Concatenate source files with separator comments."""
    parts = []
    for rel in file_list:
        path = base / rel
        if not path.exists():
            print(f"  WARNING: missing {rel} — skipped")
            continue
        content = path.read_text(encoding="utf-8")
        # Separator for debugging (stripped during minification if comments removed)
        parts.append(f"\n/* ── {rel} ── */\n")
        parts.append(content)
    return "\n".join(parts)


def build_js_bundles(minify: bool = True) -> int:
    """Build all JS bundles. Returns total bytes written."""
    try:
        import rjsmin
    except ImportError:
        print("WARNING: rjsmin not installed — JS will not be minified")
        print("  Install: pip install rjsmin")
        minify = False

    DIST_JS.mkdir(parents=True, exist_ok=True)
    total = 0

    for name, files in JS_BUNDLES:
        raw = concat_files(files, STATIC)
        if minify:
            out = rjsmin.jsmin(raw, keep_bang_comments=False)
        else:
            out = raw
        out_bytes = out.encode("utf-8")
        out_path = DIST_JS / name
        out_path.write_bytes(out_bytes)
        h = _content_hash(out_bytes)
        size_kb = len(out_bytes) / 1024
        total += len(out_bytes)
        print(f"  {name:40s} {size_kb:8.1f} KB  [{h}]  ({len(files)} files)")

    return total


def build_css_bundles(minify: bool = True) -> int:
    """Build all CSS bundles. Returns total bytes written."""
    try:
        import rcssmin
    except ImportError:
        print("WARNING: rcssmin not installed — CSS will not be minified")
        print("  Install: pip install rcssmin")
        minify = False

    DIST_CSS.mkdir(parents=True, exist_ok=True)
    total = 0

    for name, files in CSS_BUNDLES:
        raw = concat_files(files, STATIC)
        if minify:
            out = rcssmin.cssmin(raw)
        else:
            out = raw
        out_bytes = out.encode("utf-8")
        out_path = DIST_CSS / name
        out_path.write_bytes(out_bytes)
        h = _content_hash(out_bytes)
        size_kb = len(out_bytes) / 1024
        total += len(out_bytes)
        print(f"  {name:40s} {size_kb:8.1f} KB  [{h}]  ({len(files)} files)")

    return total


def clean():
    """Remove the dist/ output directories."""
    dist = STATIC / "dist"
    if dist.exists():
        shutil.rmtree(dist)
        print(f"Removed {dist}")
    else:
        print("Nothing to clean.")


def main():
    args = sys.argv[1:]

    if "--clean" in args:
        clean()
        return

    minify = "--dev" not in args
    mode = "production (minified)" if minify else "development (no minification)"

    print(f"\n{'=' * 60}")
    print(f"  Bundle Builder - {mode}")
    print(f"{'=' * 60}\n")

    t0 = time.perf_counter()

    print("JS Bundles:")
    js_total = build_js_bundles(minify)

    print()
    print("CSS Bundles:")
    css_total = build_css_bundles(minify)

    elapsed = time.perf_counter() - t0
    total_kb = (js_total + css_total) / 1024

    print(f"\n{'-' * 60}")
    print(f"  Total: {total_kb:.1f} KB in {elapsed:.2f}s")
    print(f"  Output: static/dist/js/  static/dist/css/")
    print(f"{'-' * 60}\n")


if __name__ == "__main__":
    main()
