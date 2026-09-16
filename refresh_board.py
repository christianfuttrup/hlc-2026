#!/usr/bin/env python3
"""
Refresh the HLC Event 2026 board with current numbers from the Google Sheet.

The sheet URL comes from the SHEET_CSV_URL environment variable, which the
workflow supplies from an encrypted GitHub Actions secret. It is deliberately
NOT stored in the repository: the sheet contains colleagues' names and dietary
information, and this repository is public.

Only the single `const DATA = {...};` line in docs/index.html is rewritten.
If anything looks wrong, the file is left untouched and the script exits 1.
"""

import csv
import io
import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PAGE = Path(__file__).resolve().parent.parent / "docs" / "index.html"
TZ = ZoneInfo("Europe/Copenhagen")

# Header fragments to find the Yes/No columns (matched case-insensitively).
COL_DINNER = "dinner"
COL_OVERNIGHT = "overnight"

# Guard against a truncated or half-loaded sheet wiping the board.
MIN_PLAUSIBLE_TOTAL = 40


def fail(msg: str) -> None:
    print(f"::error::{msg}")
    sys.exit(1)


def fetch(url: str) -> str:
    # Defeat caching. Without this you can be handed a stale copy of the sheet
    # and publish numbers that are days old without any error showing up.
    url += ("&" if "?" in url else "?") + "_cb=" + str(int(time.time()))
    req = urllib.request.Request(url, headers={
        "User-Agent": "hlc-board-refresh",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = resp.read()
    text = raw.decode("utf-8", errors="replace")
    if text.lstrip()[:9].lower().startswith(("<!doctype", "<html")):
        fail("Got an HTML page instead of CSV. The sheet is probably no longer "
             "shared with 'Anyone with the link'.")
    return text


def count(text: str):
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if len(rows) < 2:
        fail("Sheet appears to be empty.")

    headers = [h.strip().lower() for h in rows[0]]
    body = rows[1:]

    def col(fragment):
        for i, h in enumerate(headers):
            if fragment in h:
                return i
        fail(f"No column matching {fragment!r}. Headers were: {headers}")

    ci_dinner, ci_over = col(COL_DINNER), col(COL_OVERNIGHT)

    def yes(idx):
        return sum(
            1 for r in body
            if idx < len(r) and r[idx].strip().lower() in ("yes", "y", "true")
        )

    return {"total": len(body), "dinnerYes": yes(ci_dinner), "overnightYes": yes(ci_over)}


def main() -> None:
    url = os.environ.get("SHEET_CSV_URL", "").strip()
    if not url:
        fail("SHEET_CSV_URL is not set. Add it under "
             "Settings > Secrets and variables > Actions.")

    data = count(fetch(url))

    # Sanity checks — never publish impossible figures.
    if data["total"] < MIN_PLAUSIBLE_TOTAL:
        fail(f"Only {data['total']} rows; expected at least {MIN_PLAUSIBLE_TOTAL}. "
             "Refusing to overwrite the board.")
    for key in ("dinnerYes", "overnightYes"):
        if data[key] > data["total"]:
            fail(f"{key} ({data[key]}) exceeds total ({data['total']}).")

    data["updated"] = datetime.now(TZ).strftime("%-d %b %Y, %H:%M")

    html = PAGE.read_text(encoding="utf-8")
    new_line = (
        'const DATA = {{"total":{total},"dinnerYes":{dinnerYes},'
        '"overnightYes":{overnightYes},"updated":"{updated}"}};'
    ).format(**data)

    updated_html, n = re.subn(r"const DATA = \{.*?\};", new_line, html, count=1)
    if n != 1:
        fail("Could not find the 'const DATA = {...};' line in docs/index.html.")

    PAGE.write_text(updated_html, encoding="utf-8")
    print(f"{data['total']} registered, {data['dinnerYes']} dinner, "
          f"{data['overnightYes']} overnight ({data['updated']})")


if __name__ == "__main__":
    main()
