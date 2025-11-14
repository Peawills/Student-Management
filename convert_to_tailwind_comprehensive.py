#!/usr/bin/env python3
"""
Comprehensive Bootstrap to Tailwind conversion for all templates.
This script:
1. Replaces ALL Bootstrap Icons (bi bi-*) with placeholder inline SVG
2. Converts ALL Bootstrap utility classes to Tailwind equivalents
3. Handles Bootstrap-specific markup
"""

import os
import re
from pathlib import Path


def replace_all_bootstrap_icons(content):
    """Replace ALL Bootstrap Icon usages with placeholder Heroicons."""
    # Generic pattern to match any <i class="bi bi-*"></i>
    # This pattern handles variations like:
    # - <i class="bi bi-xxx"></i>
    # - <i class="bi bi-xxx-fill"></i>
    # - <i class="bi bi-xxx" style="..."></i>
    # - Extra classes mixed in

    def replace_icon(match):
        """Replace individual Bootstrap icon with generic Heroicon SVG."""
        full_match = match.group(0)
        icon_class = match.group(1)

        # Extract the icon name for potential future mapping
        icon_name = icon_class.replace("bi bi-", "").strip()

        # Return a generic Heroicon SVG that can be styled with Tailwind
        return f'''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 inline-block" title="{icon_name}"></svg>'''

    # Pattern to match <i class="bi bi-*"></i> with optional attributes
    # This regex handles multiple spaces, newlines, and extra classes
    pattern = r'<i\s+class=["\']([^"\']*bi\s+bi-[^\s"\']*[^"\']*)["\'][^>]*>\s*</i>'
    content = re.sub(pattern, replace_icon, content, flags=re.IGNORECASE | re.MULTILINE)

    return content


def replace_bootstrap_utilities(content):
    """Replace ALL Bootstrap utility classes with Tailwind equivalents."""
    replacements = [
        # Display utilities (most common)
        (r"\bd-none\b", "hidden"),
        (r"\bd-block\b", "block"),
        (r"\bd-inline-block\b", "inline-block"),
        (r"\bd-inline\b", "inline"),
        (r"\bd-flex\b", "flex"),
        (r"\bd-grid\b", "grid"),
        (r"\bd-table\b", "table"),
        (r"\bd-none\b", "hidden"),
        # Responsive display utilities
        (r"\bd-sm-none\b", "sm:hidden"),
        (r"\bd-sm-block\b", "sm:block"),
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
        (r"\bd-xl-none\b", "xl:hidden"),
        (r"\bd-xl-flex\b", "xl:flex"),
        # Margin utilities (end = right, start = left in Bootstrap)
        (r"\bme-0\b", "mr-0"),
        (r"\bme-1\b", "mr-1"),
        (r"\bme-2\b", "mr-2"),
        (r"\bme-3\b", "mr-3"),
        (r"\bme-4\b", "mr-4"),
        (r"\bme-5\b", "mr-5"),
        (r"\bme-auto\b", "mr-auto"),
        (r"\bms-0\b", "ml-0"),
        (r"\bms-1\b", "ml-1"),
        (r"\bms-2\b", "ml-2"),
        (r"\bms-3\b", "ml-3"),
        (r"\bms-4\b", "ml-4"),
        (r"\bms-5\b", "ml-5"),
        (r"\bms-auto\b", "ml-auto"),
        (r"\bmb-0\b", "mb-0"),
        (r"\bmb-1\b", "mb-1"),
        (r"\bmb-2\b", "mb-2"),
        (r"\bmb-3\b", "mb-3"),
        (r"\bmb-4\b", "mb-4"),
        (r"\bmb-5\b", "mb-5"),
        (r"\bmt-0\b", "mt-0"),
        (r"\bmt-1\b", "mt-1"),
        (r"\bmt-2\b", "mt-2"),
        (r"\bmt-3\b", "mt-3"),
        (r"\bmt-4\b", "mt-4"),
        (r"\bmt-5\b", "mt-5"),
        # Padding utilities (end = right, start = left in Bootstrap)
        (r"\bpe-0\b", "pr-0"),
        (r"\bpe-1\b", "pr-1"),
        (r"\bpe-2\b", "pr-2"),
        (r"\bpe-3\b", "pr-3"),
        (r"\bpe-4\b", "pr-4"),
        (r"\bpe-5\b", "pr-5"),
        (r"\bps-0\b", "pl-0"),
        (r"\bps-1\b", "pl-1"),
        (r"\bps-2\b", "pl-2"),
        (r"\bps-3\b", "pl-3"),
        (r"\bps-4\b", "pl-4"),
        (r"\bps-5\b", "pl-5"),
        # Other common utilities
        (r"\btext-muted\b", "text-gray-500"),
        (r"\btext-danger\b", "text-red-600"),
        (r"\btext-success\b", "text-green-600"),
        (r"\btext-warning\b", "text-yellow-600"),
        (r"\btext-info\b", "text-blue-600"),
        (r"\bbg-light\b", "bg-gray-100"),
        (r"\bbg-dark\b", "bg-gray-800"),
        (r"\bbg-danger\b", "bg-red-600"),
        (r"\bbg-success\b", "bg-green-600"),
        (r"\bbg-warning\b", "bg-yellow-600"),
        (r"\bbg-info\b", "bg-blue-600"),
        # Spinner (Bootstrap) -> Tailwind animation
        (r"spinner-border\s+spinner-border-sm", "inline-block animate-spin"),
        (r"spinner-border", "inline-block animate-spin"),
        # Flex utilities
        (r"\bflex-row\b", "flex-row"),
        (r"\bflex-column\b", "flex-col"),
        (r"\bjustify-content-center\b", "justify-center"),
        (r"\bjustify-content-between\b", "justify-between"),
        (r"\bjustify-content-end\b", "justify-end"),
        (r"\balign-items-center\b", "items-center"),
        (r"\balign-items-end\b", "items-end"),
        (r"\balign-items-start\b", "items-start"),
        # Text alignment
        (r"\btext-center\b", "text-center"),
        (r"\btext-start\b", "text-left"),
        (r"\btext-end\b", "text-right"),
        # Other utilities
        (r"\bw-100\b", "w-full"),
        (r"\bh-auto\b", "h-auto"),
        (r"\brounded\b", "rounded"),
        (r"\brounded-circle\b", "rounded-full"),
        (r"\bshadow\b", "shadow"),
        (r"\bshadow-sm\b", "shadow-sm"),
        (r"\bshadow-lg\b", "shadow-lg"),
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
        content = replace_all_bootstrap_icons(content)
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
    project_root = Path(
        "c:\\Users\\Williams Peaceful\\Portfolio\\Djangoproject\\Studentmanagement"
    )

    print("🔄 Starting comprehensive Tailwind conversion...\n")

    # Find all .html files except env
    html_files = sorted(
        [
            f
            for f in project_root.rglob("*.html")
            if "env" not in str(f) and ".git" not in str(f)
        ]
    )

    converted = 0
    skipped = 0
    errors = 0

    for html_file in html_files:
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
