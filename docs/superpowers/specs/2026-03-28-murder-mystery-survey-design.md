# Murder Mystery Survey App — Design Spec

**Date:** 2026-03-28

## Overview

A Flask web app for a murder mystery party. Guests fill out a survey on their phones via QR code. A host-facing dashboard shows who has/hasn't responded and flags duplicates. A slideshow displays each character's responses, intended to be cast to a TV via Chromecast.

---

## Architecture

- **Framework:** Flask (Python)
- **Database:** PostgreSQL (managed, via Railway)
- **Hosting:** Railway (deployed via GitHub push)
- **Config:** `config.yaml` — defines character names and survey questions; read once at app startup and cached in memory. If `config.yaml` is missing or malformed, the app raises an error on startup and refuses to serve requests.

### Dependencies (`requirements.txt`)

```
Flask
Flask-SQLAlchemy
psycopg2-binary
qrcode[pil]
PyYAML
gunicorn
python-dotenv
```

---

## Config File (`config.yaml`)

Located at the project root. Loaded once on startup.

```yaml
characters:
  - Lord Blackwood
  - Lady Crimson
  - Col. Mustard
  - Miss Scarlet
  # ... up to 20 characters

questions:
  - id: name
    text: "What's your name?"
    type: dropdown        # populated from characters list
  - id: accuse
    text: "Who do you accuse of murder?"
    type: dropdown
  - id: why
    text: "Why do you accuse them?"
    type: text
  - id: best_dressed
    text: "Who was best dressed?"
    type: dropdown
  - id: best_actor
    text: "Who was the best actor/actress?"
    type: dropdown
  - id: money
    text: "How much money did you end with?"
    type: text
  - id: how_money
    text: "How did you get/lose your money?"
    type: text
```

Question types: `dropdown` (uses the `characters` list) or `text` (free text input). Question list order drives both form rendering and slideshow display. The question with `id: name` is special — its submitted value is extracted and stored in `character_name` on the DB row.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Injected by Railway. Must be rewritten from `postgres://` to `postgresql+psycopg2://` for SQLAlchemy compatibility. |
| `DASHBOARD_PIN` | PIN for dashboard access (e.g. `1234`). Set in Railway environment settings. |
| `PUBLIC_URL` | The app's public Railway URL (e.g. `https://murder-mystery.up.railway.app`). Used to generate the QR code. Set in Railway environment settings. |

For local development, create a `.env` file at the project root:

```
DATABASE_URL=postgresql+psycopg2://localhost/murder_mystery
DASHBOARD_PIN=1234
PUBLIC_URL=http://localhost:5000
```

---

## Database

Single table: `responses`

| Column | Type | Notes |
|---|---|---|
| id | integer | Primary key, auto-increment |
| character_name | string | Extracted from the answer to question `id: name` |
| answers | JSON | Dict keyed by question `id`, contains all answers including `name` |
| submitted_at | timestamp | UTC, set on insert |
| is_duplicate | boolean | `true` if another response for this `character_name` already existed at time of submission |

---

## Pages

### `/survey`

- Public, no auth required
- Mobile-optimised: large tap targets, readable font, no horizontal scroll
- Renders the survey form dynamically from `config.yaml` in question list order
- Dropdowns populated from `characters` list; free text inputs for `text` type questions
- The `name` question (dropdown) is required — form cannot be submitted without it
- On submit:
  - Extracts `character_name` from the answer to question `id: name`
  - Checks if a response for that `character_name` already exists in the DB
  - If yes: saves new response with `is_duplicate = true`
  - If no: saves with `is_duplicate = false`
  - Redirects to `/thank-you`

### `/thank-you`

- Static page shown after a successful submission
- If the submission was a duplicate: displays "Thanks [character name] — looks like you may have already submitted. Your response was recorded but flagged for review."
- If not a duplicate: displays "Thanks [character name]! Your response has been recorded."

### `/dashboard/login`

- Simple form with a single PIN field
- On correct PIN: sets `session['authenticated'] = True` (session lifetime: browser session, expires on close)
- On incorrect PIN: re-renders the form with an error message. No lockout.
- Redirects to `/dashboard` on success

### `/dashboard`

- Requires `session['authenticated'] = True`; redirects to `/dashboard/login` if not set
- Reconciliation logic: iterate over the `characters` list from `config.yaml`; for each, check whether a `responses` row exists with that `character_name`
- Displays:
  - QR code generated from `PUBLIC_URL + "/survey"` using `qrcode` library, rendered as an inline PNG
  - **Submitted** column: character names with a green dot; if `is_duplicate` exists for that character, show ⚠ and the duplicate count
  - **Pending** column: character names with a grey dot
  - CSV export button — `GET /dashboard/export`
  - "View Slideshow" button linking to `/slideshow`
- Layout: QR code centered at top, two-column submitted/pending list below, export + slideshow buttons at bottom

### `/dashboard/export`

- Requires `session['authenticated'] = True`
- Returns a CSV file download (`Content-Disposition: attachment`)
- CSV format:
  - One row per response (including duplicates)
  - Columns: `submitted_at`, `character_name`, `is_duplicate`, then one column per question in config order, using question `text` as the header
  - Characters with no submission are not included
  - Timestamps in ISO 8601 format (UTC)

### `/slideshow`

- No auth (relies on obscurity; intended for Chromecast casting)
- Shows only characters who have submitted (at least one response); ordered by position in `config.yaml` `characters` list
- For characters with duplicate submissions: show the most recent response only
- One slide per submitted character, navigated via prev/next buttons
- Each slide layout (fixed to current question set by `id`):
  - Character name as heading
  - `accuse` + `why` answers span full width (two stacked cells)
  - `best_dressed`, `best_actor`, `money`, `how_money` in a 2×2 grid
  - X / Y counter (X = current slide position, Y = total submitted count)
- Prev/next buttons navigate between characters

---

## Deployment

1. Create a free Railway account and connect the GitHub repo
2. Add a PostgreSQL plugin in Railway (one click) — Railway injects `DATABASE_URL` automatically
3. Set `DASHBOARD_PIN` and `PUBLIC_URL` as environment variables in Railway settings
4. Add a `Procfile` at the project root:
   ```
   web: gunicorn app:app
   ```
5. Push to GitHub — Railway auto-deploys on push
6. Run `flask db upgrade` (or equivalent table creation) once after first deploy

---

## Local Development

1. Install dependencies: `pip install -r requirements.txt`
2. Create `.env` with `DATABASE_URL`, `DASHBOARD_PIN`, `PUBLIC_URL`
3. Create a local Postgres database: `createdb murder_mystery`
4. Run: `flask run`

---

## Out of Scope

- User accounts or authentication beyond a PIN
- Editing or deleting submissions
- Real-time updates (page refresh is sufficient for this use case)
- Mobile-optimised slideshow controls (Chromecast casts a desktop Chrome tab)
- Lockout after failed PIN attempts
