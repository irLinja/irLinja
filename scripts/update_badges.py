#!/usr/bin/env python3
"""Fetch Credly badges and update the README badges section."""

import json
import sys
import urllib.request
from pathlib import Path

CREDLY_USER = "arash"
BADGES_URL = f"https://www.credly.com/users/{CREDLY_USER}/badges.json"
README_PATH = Path(__file__).resolve().parent.parent / "README.md"
START_MARKER = "<!-- CREDLY_BADGES_START -->"
END_MARKER = "<!-- CREDLY_BADGES_END -->"

# Display order for known issuers. Unlisted issuers appear last, sorted alphabetically.
ISSUER_ORDER = ["The Linux Foundation", "IBM", "Isovalent"]


def fetch_badges():
    req = urllib.request.Request(BADGES_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["data"]


def issuer_name(badge):
    try:
        return badge["badge_template"]["issuer"]["entities"][0]["entity"]["name"]
    except (KeyError, IndexError):
        return "Other"


def group_badges(badges):
    groups = {}
    for badge in badges:
        issuer = issuer_name(badge)
        groups.setdefault(issuer, []).append(badge)

    # Sort each group by issued_at descending (newest first)
    for group in groups.values():
        group.sort(key=lambda b: b.get("issued_at_date", ""), reverse=True)

    # Order groups: known issuers first (by ISSUER_ORDER), then unknown alphabetically
    known = {name: groups.pop(name) for name in ISSUER_ORDER if name in groups}
    unknown = dict(sorted(groups.items()))
    return {**known, **unknown}


def badge_html(badge):
    badge_id = badge["id"]
    tmpl = badge["badge_template"]
    name = tmpl["name"]
    image_url = tmpl["image_url"]
    return (
        f'<a href="https://www.credly.com/badges/{badge_id}/public_url">'
        f'<img height="90" width="90" src="{image_url}" alt="{name}"/></a>'
    )


def render_section(grouped):
    lines = ["### Certificates & Badges", ""]
    for issuer, badges in grouped.items():
        lines.append(f"**{issuer}**")
        lines.append("")
        lines.append(" ".join(badge_html(b) for b in badges))
        lines.append("")
    return "\n".join(lines)


def update_readme(section_content):
    readme = README_PATH.read_text()

    start = readme.find(START_MARKER)
    end = readme.find(END_MARKER)
    if start == -1 or end == -1:
        print("ERROR: Marker comments not found in README.md", file=sys.stderr)
        sys.exit(1)

    new_content = (
        readme[: start + len(START_MARKER)]
        + "\n"
        + section_content
        + readme[end:]
    )

    if new_content == readme:
        print("No changes needed.")
        return

    README_PATH.write_text(new_content)
    print(f"README.md updated with badges.")


def main():
    try:
        badges = fetch_badges()
    except Exception as e:
        print(f"WARNING: Failed to fetch badges: {e}", file=sys.stderr)
        print("Keeping existing README content.")
        sys.exit(0)

    grouped = group_badges(badges)
    section = render_section(grouped)
    update_readme(section)


if __name__ == "__main__":
    main()
