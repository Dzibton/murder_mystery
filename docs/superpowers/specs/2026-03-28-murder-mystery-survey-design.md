# Murder Mystery Survey App — Design Spec

**Date:** 2026-03-28

## Overview

A Flask web app for a murder mystery party. Guests fill out a survey on their phones via QR code. A host-facing dashboard shows who has/hasn't responded and flags duplicates. A slideshow displays each character's responses, intended to be cast to a TV via Chromecast.

---

## Architecture

- **Framework:** Flask (Python)
- **Database:** PostgreSQL (managed, via Railway)
- **Hosting:** Railway (deployed via GitHub push)
- **Config:** `config.yaml` — defines character names and survey questions; read at app startup

---

## Config File (`config.yaml`)

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

Question types: `dropdown` (uses the `characters` list) or `text` (free text input). The question list is the source of truth for form rendering order and slideshow display order.

---

## Database

Single table: `responses`

| Column | Type | Notes |
|---|---|---|
| id | integer | Primary key, auto-increment |
| character_name | string | Must match a name in config |
| answers | JSON | Dict keyed by question `id` |
| submitted_at | timestamp | UTC, set on insert |
| is_duplicate | boolean | `true` if another response for this character already existed at time of submission |

---

## Pages

### `/survey`
- Public, no auth required
- Renders the survey form dynamically from `config.yaml`
- Dropdowns populated from `characters` list; free text fields for `text` type questions
- On submit:
  - Checks if a response for that character already exists
  - If yes: saves with `is_duplicate = true`
  - Saves response to DB
  - Redirects to a thank-you page

### `/dashboard`
- Protected by a simple PIN (set via environment variable)
- Displays:
  - QR code linking to `/survey` (the public Railway URL)
  - Two columns: **Submitted** (green dot, ⚠ flag + count for duplicates) and **Pending** (grey)
  - CSV export button — downloads all responses as a flat CSV
  - "View Slideshow" button linking to `/slideshow`
- Layout: QR code centered at top, two-column list below, slideshow button at bottom

### `/slideshow`
- No auth (relies on obscurity; intended for casting)
- One slide per character who has submitted
- Each slide shows all answers in a compact grid:
  - Accusation + reason span full width
  - Best dressed, best actor, money amount, money explanation in two-column grid
- Prev/next navigation buttons
- X/20 counter (X = position among submitted characters)
- If a character has duplicate submissions, shows the most recent one

---

## Deployment

- Hosted on Railway
- PostgreSQL added as a Railway plugin (one click, connection string injected as `DATABASE_URL` env var)
- Dashboard PIN stored as `DASHBOARD_PIN` environment variable in Railway settings
- Deployed via `git push` to GitHub (Railway auto-deploys on push)
- `requirements.txt` tracks all dependencies

---

## Out of Scope

- User accounts or authentication beyond a PIN
- Editing or deleting submissions
- Real-time updates (page refresh is sufficient for this use case)
- Mobile-optimised slideshow controls (Chromecast casts a desktop Chrome tab)
