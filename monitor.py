import difflib
import hashlib
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

PAGES = [
    {
        "name": "Virginia DEQ Carbon Trading",
        "url": "https://www.deq.virginia.gov/air-energy/greenhouse-gases/carbon-trading",
    },
    {
        "name": "RGGI New Participation",
        "url": "https://www.rggi.org/program-overview-and-design/new-participation",
    },
    {
        "name": "RGGI Releases",
        "url": "https://www.rggi.org/news-releases/rggi-releases",
    },
    {
        "name": "Virginia Town Hall Chapter 1751",
        "url": "https://townhall.virginia.gov/l/ViewChapter.cfm?ChapterID=1751",
    },
]

SUBJECT = "MV Carbon Tracker: RGGI Website Changes"

EMAIL_SENDER = "moleculecarbonnews@gmail.com"
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_RECEIVERS = [
    "grant@molecule-ventures.com",
    "anna@molecule-ventures.com",
    "nick@molecule-ventures.com",
]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

STATE_DIR = "state"


def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def fetch_central_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MVCarbonTracker/1.0)"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "noscript",
        "svg",
    ]):
        tag.decompose()

    selectors = [
        "main",
        "article",
        "#main-content",
        "#content",
        ".main-content",
        ".region-content",
        "#block-system-main",
        ".field--name-body",
        ".node__content",
        ".view-content",
        ".content",
        "body",
    ]

    content = None

    for selector in selectors:
        content = soup.select_one(selector)
        if content:
            break

    if content is None:
        content = soup.body or soup

    text = content.get_text("\n", strip=True)

    lines = [line.strip() for line in text.splitlines()]
    lines = [re.sub(r"\s+", " ", line) for line in lines]
    lines = [line for line in lines if line]

    return "\n".join(lines)


def make_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_file(path):
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(value)


def page_state_paths(page):
    parsed = urlparse(page["url"])
    slug = slugify(f"{page['name']}-{parsed.netloc}-{parsed.path}")

    hash_path = os.path.join(STATE_DIR, f"{slug}.hash.txt")
    text_path = os.path.join(STATE_DIR, f"{slug}.text.txt")

    return hash_path, text_path


def make_diff(old_text, new_text):
    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile="Previous version",
        tofile="Current version",
        lineterm="",
    )

    return "\n".join(diff)


def send_email(changes):
    msg = EmailMessage()

    msg["Subject"] = SUBJECT
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECEIVERS)

    sections = [
        "The MV Carbon Tracker detected changes on the following monitored webpage(s):",
        "",
    ]

    for change in changes:
        diff_text = change["diff"]

        if len(diff_text) > 12000:
            diff_text = diff_text[:12000] + "\n\n[Diff truncated because it was too long.]"

        sections.extend([
            "=" * 80,
            change["name"],
            change["url"],
            "=" * 80,
            "",
            diff_text,
            "",
        ])

    msg.set_content("\n".join(sections))

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)


def main():
    changes = []

    for page in PAGES:
        print(f"Checking: {page['name']}")

        current_text = fetch_central_content(page["url"])
        current_hash = make_hash(current_text)

        hash_path, text_path = page_state_paths(page)

        old_hash = read_file(hash_path)
        old_text = read_file(text_path)

        if old_hash is None or old_text is None:
            write_file(hash_path, current_hash)
            write_file(text_path, current_text)
            print(f"Initial version saved: {page['name']}")
            continue

        if old_hash != current_hash:
            diff_text = make_diff(old_text, current_text)

            changes.append({
                "name": page["name"],
                "url": page["url"],
                "diff": diff_text,
            })

            write_file(hash_path, current_hash)
            write_file(text_path, current_text)

            print(f"Change detected: {page['name']}")
        else:
            print(f"No change: {page['name']}")

    if changes:
        send_email(changes)
        print(f"Email sent for {len(changes)} changed page(s).")
    else:
        print("No changes detected across monitored pages.")


if __name__ == "__main__":
    main()
