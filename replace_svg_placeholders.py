#!/usr/bin/env python3
"""
Replace generic SVG placeholders with actual Heroicon SVG path content.
Searches for <svg ... title="icon-name"></svg> patterns and replaces them using a mapping.
"""

import re
from pathlib import Path

# Mapping: title attribute -> full <svg ...>...</svg> string (Heroicons outline/solid)
# These are simplified, valid Heroicon SVGs (outline style) that use stroke/currentColor where appropriate.
MAPPING = {
    # basic/common
    "users": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a4 4 0 00-4-4h-1"/><path stroke-linecap="round" stroke-linejoin="round" d="M9 20H4v-2a4 4 0 014-4h1"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 12a4 4 0 100-8 4 4 0 000 8z"/></svg>',
    "people-fill": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 inline-block"><path d="M16 11c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM6 11c1.657 0 3-1.343 3-3S7.657 5 6 5 3 6.343 3 8s1.343 3 3 3zM6 13c-2.33 0-7 1.167-7 3.5V19h20v-2.5C22 14.167 17.33 13 15 13H6z"/></svg>',
    "chart-bar": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M3 3v18h18"/><path stroke-linecap="round" stroke-linejoin="round" d="M7 13v6"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v10"/><path stroke-linecap="round" stroke-linejoin="round" d="M17 5v14"/></svg>',
    "chevron-down": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" class="w-4 h-4 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M6 8l4 4 4-4"/></svg>',
    "exclamation-triangle": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 17h.01"/></svg>',
    "academic-cap": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-6 h-6 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M12 14l9-5-9-5-9 5 9 5z"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 14v7"/><path stroke-linecap="round" stroke-linejoin="round" d="M5 18v-6"/></svg>',
    "bookmark": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M5 5v14l7-5 7 5V5z"/></svg>',
    "cog": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0a1.724 1.724 0 002.605 1.028c.807-.543 1.931.24 1.545 1.146a1.724 1.724 0 001.03 2.604c.921.3.921 1.603 0 1.902a1.724 1.724 0 00-1.028 2.605c.543.807-.24 1.931-1.146 1.545a1.724 1.724 0 00-2.604 1.03c-.3.921-1.603.921-1.902 0a1.724 1.724 0 00-2.605-1.028c-.807.543-1.931-.24-1.545-1.146a1.724 1.724 0 00-1.03-2.604c-.921-.3-.921-1.603 0-1.902a1.724 1.724 0 001.028-2.605c-.543-.807.24-1.931 1.146-1.545.982.33 2.07-.256 2.605-1.028z"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 inline-block"><path d="M12 21s-6.716-4.35-9.028-7.05C-0.5 10.75 3.5 4 8 4c2.21 0 4 1.79 4 4s1.79-4 4-4c4.5 0 8.528 6.75 5.028 9.95C18.716 16.65 12 21 12 21z"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M3 9.75L12 3l9 6.75V21a.75.75 0 01-.75.75H3.75A.75.75 0 013 21V9.75z"/></svg>',
    "currency-dollar": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8c1.657 0 3 1.343 3 3s-1.343 3-3 3m0-6V5m0 14v-2"></path></svg>',
    "megaphone": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M4 10v4a2 2 0 002 2h1l5 3V5L7 8H6a2 2 0 00-2 2z"/></svg>',
    "envelope": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M3 8l9 6 9-6"/><path stroke-linecap="round" stroke-linejoin="round" d="M21 8v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8"/></svg>',
    "arrow-right": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-4 h-4 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M12 5l7 7-7 7"/></svg>',
    "lock-closed": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><rect width="14" height="10" x="5" y="11" rx="2"/><path stroke-linecap="round" stroke-linejoin="round" d="M8 11V8a4 4 0 118 0v3"/></svg>',
    "eye": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5s8.268 2.943 9.542 7c-1.274 4.057-5.065 7-9.542 7S3.732 16.057 2.458 12z"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7z"/></svg>',
    "trash": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M3 6h18"/><path stroke-linecap="round" stroke-linejoin="round" d="M8 6v12a2 2 0 002 2h4a2 2 0 002-2V6"/><path stroke-linecap="round" stroke-linejoin="round" d="M10 11v6M14 11v6"/><path stroke-linecap="round" stroke-linejoin="round" d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>',
    "plus-circle": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><circle cx="12" cy="12" r="9"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v8M8 12h8"/></svg>',
    "magnifying-glass": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35"/><path stroke-linecap="round" stroke-linejoin="round" d="M11 18a7 7 0 100-14 7 7 0 000 14z"/></svg>',
    "calendar": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><rect x="3" y="4" width="18" height="18" rx="2"/><path stroke-linecap="round" stroke-linejoin="round" d="M16 2v4M8 2v4M3 10h18"/></svg>',
    "document-plus": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path stroke-linecap="round" stroke-linejoin="round" d="M14 2v6h6"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 11v6M9 14h6"/></svg>',
    "cloud-arrow-up": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16a4 4 0 014-4h1"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 12v6"/><path stroke-linecap="round" stroke-linejoin="round" d="M9 15l3-3 3 3"/></svg>',
    "photo": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><rect width="18" height="14" x="3" y="5" rx="2"/><path stroke-linecap="round" stroke-linejoin="round" d="M3 7l7 6 4-3 7 6"/></svg>',
    "document-text": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path stroke-linecap="round" stroke-linejoin="round" d="M14 2v6h6"/><path stroke-linecap="round" stroke-linejoin="round" d="M8 13h8M8 17h8"/></svg>',
    "clock": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-5 h-5 inline-block"><circle cx="12" cy="12" r="9"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 7v6l4 2"/></svg>',
    "hashtag": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="w-4 h-4 inline-block"><path stroke-linecap="round" stroke-linejoin="round" d="M7 6h10M7 18h10M11 6l-2 12M15 6l-2 12"/></svg>',
}


def replace_in_file(path: Path):
    text = path.read_text(encoding="utf-8")
    # regex to find svg tags with a title attribute: capture title value
    pattern = re.compile(
        r"(<svg[^>]*\btitle=\"([^\"]+)\"[^>]*>\s*)(?:</svg>)", re.IGNORECASE
    )
    replaced = 0

    def repl(m):
        nonlocal replaced
        full = m.group(0)
        prefix = m.group(1)
        title = m.group(2).strip()
        key = title
        # Some code used composite titles like 'file-earmark-plus text-primary-500' -> keep first token
        key = key.split()[0]
        if key in MAPPING:
            replaced += 1
            return MAPPING[key]
        else:
            # If unknown, keep original but add a comment to help manual mapping later
            return full + f"<!-- UNMAPPED_ICON:{key} -->"

    new_text = pattern.sub(repl, text)
    if replaced > 0:
        path.write_text(new_text, encoding="utf-8")
    return replaced


def main():
    root = Path(__file__).parent
    html_files = [
        p for p in root.rglob("*.html") if "env" not in str(p) and ".git" not in str(p)
    ]
    total_replaced = 0
    file_changes = []
    unmapped = set()

    for f in sorted(html_files):
        r = replace_in_file(f)
        if r > 0:
            file_changes.append((f.relative_to(root), r))
            total_replaced += r

    print(f"Replaced {total_replaced} placeholder SVGs in {len(file_changes)} files")
    for fn, c in file_changes:
        print(f"  {fn}: {c}")


if __name__ == "__main__":
    main()
