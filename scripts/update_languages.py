import os
from collections import defaultdict
from pathlib import Path

import requests


USERNAME = "kishorkarthik"
README = Path("README.md")

API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
}


def get_repositories():
    repositories = []
    page = 1

    while True:
        response = requests.get(
            f"{API}/user/repos",
            headers=HEADERS,
            params={
                "visibility": "public",
                "affiliation": "owner",
                "per_page": 100,
                "page": page,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            break

        repositories.extend(data)
        page += 1

    return repositories


def get_languages(repository):
    response = requests.get(
        f"{API}/repos/{repository['full_name']}/languages",
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def calculate_distribution():
    totals = defaultdict(int)

    for repository in get_repositories():
        # Ignore forked repositories.
        if repository["fork"]:
            continue

        languages = get_languages(repository)

        for language, byte_count in languages.items():
            totals[language] += byte_count

    total_bytes = sum(totals.values())

    if total_bytes == 0:
        return []

    distribution = []

    for language, byte_count in totals.items():
        percentage = byte_count / total_bytes * 100

        # Ignore insignificant languages.
        if percentage >= 1:
            distribution.append((language, percentage))

    distribution.sort(key=lambda item: item[1], reverse=True)

    # Keep the README compact.
    return distribution[:8]


def update_readme(distribution):
    start_marker = "<!-- LANGUAGES:START -->"
    end_marker = "<!-- LANGUAGES:END -->"

    text = README.read_text(encoding="utf-8")

    before, remainder = text.split(start_marker, 1)
    _, after = remainder.split(end_marker, 1)

    if distribution:
        lines = [
            f"- {language} — {percentage:.1f}%"
            for language, percentage in distribution
        ]
    else:
        lines = ["- No language data available"]

    content = "\n".join(lines)

    updated = (
        before
        + start_marker
        + "\n"
        + content
        + "\n"
        + end_marker
        + after
    )

    README.write_text(updated, encoding="utf-8")


def main():
    distribution = calculate_distribution()
    update_readme(distribution)


if __name__ == "__main__":
    main()
