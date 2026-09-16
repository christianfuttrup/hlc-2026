# HLC Event 2026 — registration board

A single-page wall display for the office TVs, showing sign-ups for HLC Event 2026
(Friday 23 October 2026) and a countdown to the sign-up deadline (Monday 12 October).

A scheduled GitHub Action reads the registration sheet every 3 hours and commits the
current numbers into the page. GitHub Pages serves it.

## ⚠️ Read this first — why the sheet URL is not in this repo

Pages on a free personal account requires a **public** repository, so everything
committed here is world-readable.

The registration sheet contains colleagues' names, departments, travel plans and
dietary restrictions. It is shared "anyone with the link", which means **the link is
the password**. If it were committed here, anyone could read the whole sheet.

So the URL lives only in an encrypted Actions secret, and the published page contains
nothing but three aggregate numbers. Please keep it that way — don't paste the sheet
URL into the HTML, the workflow, or a commit message.

## Setup (once)

1. **Create a public repository** on GitHub and copy these files into it:

   ```
   .github/workflows/refresh-board.yml
   scripts/refresh_board.py
   docs/index.html
   README.md
   ```

2. **Add the sheet URL as a secret.**
   Settings → Secrets and variables → Actions → *New repository secret*
   - Name: `SHEET_CSV_URL`
   - Value: the sheet's CSV export URL (the `.../gviz/tq?tqx=out:csv&gid=0` one)

3. **Turn on Pages.**
   Settings → Pages → Source: *Deploy from a branch* → Branch: `main`, folder: `/docs`
   → Save. The URL appears on that page after the first deploy.

4. **Run it once.** Actions tab → *Refresh registration board* → *Run workflow*.
   You should see a line like `62 registered, 46 dinner, 41 overnight`.

5. **Point the TVs** at the Pages URL in full-screen / kiosk mode. The screens only
   ever talk to GitHub — they don't need access to Google.

## Changing the wording, dates or deadline

Everything editable sits at the top of the `<script>` block in `docs/index.html`:
`EVENT_NAME`, `EVENT_WHEN`, `DEADLINE`, `DEADLINE_T`, `CTA_LEAD`, `CTA_NOTE`, `CTA_HELP`.
The countdown is calculated in the browser from `DEADLINE`, so it stays right on a
screen that has been up for weeks: it shows "1 day left", then "Today — last chance",
then "Closed".

Don't hand-edit the `const DATA = {...};` line — the Action rewrites it.

## If the numbers stop updating

Check the Actions tab. The script deliberately fails, and leaves the board untouched,
if the sheet can't be read, returns fewer than 40 rows, or returns impossible figures —
a stale board is better than a blank or wrong one. The most likely cause is the sheet's
sharing being tightened; it must stay "Anyone with the link — Viewer".

Note that GitHub disables scheduled workflows in repositories with no activity for
60 days. Not a concern before October, but worth knowing.

## After the event

Delete the repository, or at least remove the `SHEET_CSV_URL` secret and disable the
workflow.
