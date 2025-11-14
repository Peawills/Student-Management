#!/usr/bin/env python3
"""
Convert all Django templates from Bootstrap + Bootstrap Icons to Tailwind CSS + Heroicons.
"""

import os
import re
from pathlib import Path

# Define icon mappings: Bootstrap Icons -> Heroicons (SVG names)
ICON_MAPPINGS = {
    "bi bi-mortarboard-fill": "academic-cap",
    "bi bi-list": "bars-3",
    "bi bi-speedometer2": "chart-bar",
    "bi bi-people-fill": "users",
    "bi bi-chevron-down": "chevron-down",
    "bi bi-exclamation-triangle-fill": "exclamation-triangle",
    "bi bi-mortarboard": "academic-cap",
    "bi bi-journal-bookmark-fill": "bookmark",
    "bi bi-person-gear": "cog-6-tooth",
    "bi bi-person-badge": "identification",
    "bi bi-person-hearts": "heart",
    "bi bi-house-heart": "home",
    "bi bi-cash-coin": "currency-dollar",
    "bi bi-megaphone": "megaphone",
    "bi bi-person-vcard": "user",
    "bi bi-envelope": "envelope",
    "bi bi-box-arrow-right": "arrow-right-end-on-rectangle",
    "bi bi-box-arrow-in-right": "arrow-right-start-on-rectangle",
    "bi bi-shield-lock": "lock-closed",
    "bi bi-person": "user",
    "bi bi-info-circle-fill": "information-circle",
    "bi bi-x-circle": "x-circle",
    "bi bi-trash": "trash-2",
    "bi bi-hourglass-split": "clock",
    "bi bi-gender-male": "arrow-up-right",
    "bi bi-gender-female": "arrow-down-left",
    "bi bi-arrow-left-circle": "arrow-left-circle",
    "bi bi-cloud-upload": "cloud-arrow-up",
    "bi bi-file-earmark-plus": "document-plus",
    "bi bi-cloud-arrow-up": "cloud-arrow-up",
    "bi bi-upload": "arrow-up-tray",
    "bi bi-files": "document-duplicate",
    "bi bi-file-image": "photo",
    "bi bi-file-earmark-pdf": "document-text",
    "bi bi-file-earmark-text": "document-text",
    "bi bi-calendar3": "calendar",
    "bi bi-hdd": "server-stack",
    "bi bi-eye": "eye",
    "bi bi-inbox": "inbox",
    "bi bi-plus-circle": "plus-circle",
    "bi bi-pencil": "pencil",
    "bi bi-check-circle": "check-circle",
    "bi bi-dash-circle": "minus-circle",
    "bi bi-download": "arrow-down-tray",
    "bi bi-search": "magnifying-glass",
    "bi bi-arrow-up": "arrow-up",
    "bi bi-arrow-down": "arrow-down",
}


def heroicon_svg(icon_name, size="20"):
    """Generate a Heroicon SVG inline."""
    # Simplified Heroicon SVG template (solid version)
    # In production, you'd fetch the actual SVG from Heroicons
    return f'<svg class="w-{size} h-{size} inline" fill="currentColor" viewBox="0 0 24 24"></svg>'


def replace_bootstrap_icons(content):
    """Replace Bootstrap Icons with Heroicon equivalents."""
    for bs_icon, heroicon in ICON_MAPPINGS.items():
        # Match: <i class="bi bi-xxx"></i> or <i class="bi bi-xxx "></i>
        pattern = rf'<i\s+class=["\']bi\s+{re.escape(bs_icon.replace("bi bi-", ""))}["\']>\s*</i>'
        replacement = f'<span class="inline-flex items-center justify-center w-5 h-5"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg></span>'
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    return content


def replace_bootstrap_utilities(content):
    """Replace Bootstrap utility classes with Tailwind equivalents."""
    replacements = [
        # Display utilities
        (r"\bd-none\b", "hidden"),
        (r"\bd-block\b", "block"),
        (r"\bd-inline\b", "inline"),
        (r"\bd-inline-block\b", "inline-block"),
        (r"\bd-flex\b", "flex"),
        (r"\bd-grid\b", "grid"),
        (r"\bd-md-none\b", "md:hidden"),
        (r"\bd-md-block\b", "md:block"),
        (r"\bd-md-inline\b", "md:inline"),
        (r"\bd-md-inline-block\b", "md:inline-block"),
        (r"\bd-md-flex\b", "md:flex"),
        (r"\bd-md-grid\b", "md:grid"),
        (r"\bd-lg-none\b", "lg:hidden"),
        (r"\bd-lg-block\b", "lg:block"),
        (r"\bd-lg-inline\b", "lg:inline"),
        (r"\bd-lg-flex\b", "lg:flex"),
        # Margin utilities
        (r"\bme-0\b", "mr-0"),
        (r"\bme-1\b", "mr-1"),
        (r"\bme-2\b", "mr-2"),
        (r"\bme-3\b", "mr-3"),
        (r"\bme-4\b", "mr-4"),
        (r"\bme-5\b", "mr-5"),
        (r"\bms-0\b", "ml-0"),
        (r"\bms-1\b", "ml-1"),
        (r"\bms-2\b", "ml-2"),
        (r"\bms-3\b", "ml-3"),
        (r"\bms-4\b", "ml-4"),
        (r"\bms-5\b", "ml-5"),
        # Spinner (Bootstrap) -> Tailwind animation
        (r"spinner-border\s+spinner-border-sm", "inline-block animate-spin"),
        (r"spinner-border", "inline-block animate-spin"),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    return content


def convert_template_file(filepath):
    """Convert a single template file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Apply transformations
        original_content = content
        content = replace_bootstrap_icons(content)
        content = replace_bootstrap_utilities(content)

        # Only write if changes were made
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True, "Converted"
        return False, "No changes"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Main conversion routine."""
    project_root = Path(__file__).parent
    templates_dir = project_root / "*/templates"

    print("🔄 Starting Tailwind conversion...\n")

    # Find all .html files
    html_files = list(project_root.rglob("*.html"))

    converted = 0
    skipped = 0
    errors = 0

    for html_file in sorted(html_files):
        # Skip certain system files
        if any(skip in str(html_file) for skip in [".git", "__pycache__", "env/"]):
            continue

        success, msg = convert_template_file(str(html_file))
        relative_path = html_file.relative_to(project_root)

        if success:
            print(f"✅ {relative_path}")
            converted += 1
        else:
            if "No changes" in msg:
                skipped += 1
            else:
                print(f"❌ {relative_path}: {msg}")
                errors += 1

    print(f"\n📊 Summary:")
    print(f"  ✅ Converted: {converted}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Errors: {errors}")
    print(f"\n✨ Conversion complete!")


if __name__ == "__main__":
    main()
