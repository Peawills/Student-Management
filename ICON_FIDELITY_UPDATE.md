# Icon Fidelity Update

Summary of the recent icon fidelity work (Nov 14, 2025):

- Replaced generic/empty SVG placeholders with full inline Heroicon SVGs.
- Total replacements: 97 placeholder SVGs replaced.
- Files changed: 38 templates (examples below).

Examples of updated files:
- `records/templates/records/base.html` (9 icons)
- `records/templates/records/homepage.html` (8 icons)
- `records/templates/records/admin_dashboard.html` (5 icons)
- `records/templates/records/student_detail.html` (4 icons)
- `records/templates/records/upload_document.html` (3 icons)
- `academics/templates/academics/classroom_detail.html` (6 icons)
- `portal/templates/portal/base.html` (2 icons)
- many more across `academics/`, `accounts/`, `committee/`, and `portal/`.

Notes & next steps:
- These inline SVGs use `currentColor` and Tailwind utility classes for sizing (e.g. `w-5 h-5`). You can override color with `text-primary-600` etc.
- If you want solid vs outline variants for specific icons, tell me which pages or icons to prioritize and I will switch the SVG paths accordingly.
- If you prefer to pull Heroicons from a CDN or as SVG components, I can adapt the templates to include an icon include and reduce duplication.

If you'd like, I can now:
- Auto-select solid/outline per icon based on semantic usage (e.g., action buttons use solid, decorative uses use outline).
- Replace icons on a per-page basis with customized sizes/colors.
- Create a small `icons/` include to centralize icon definitions and make future swaps trivial.
