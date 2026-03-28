# Deploying to Railway

## One-time setup

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo** → select `murder_mystery`
3. In the project, click **+ New** → **Database** → **Add PostgreSQL**
4. Railway will inject `DATABASE_URL` automatically — no action needed

## Environment variables to set in Railway

In your Railway web service settings → **Variables**, add:

| Variable | Value |
|---|---|
| `DASHBOARD_PIN` | Your chosen PIN (e.g. `1234`) |
| `PUBLIC_URL` | Your Railway app URL (e.g. `https://murder-mystery.up.railway.app`) — find this under Settings → Domains |
| `SECRET_KEY` | A long random string (e.g. run `python -c "import secrets; print(secrets.token_hex(32))"`) |

> **Note:** `DATABASE_URL` is injected by Railway automatically — do not set it manually.

## Deploy

Push to GitHub — Railway auto-deploys on every push to `master`:

```bash
git push origin master
```

Watch the deploy logs in the Railway dashboard. If it fails, check the **Logs** tab.

## After first deploy

1. Visit `https://your-app.up.railway.app/survey` — you should see the survey form
2. Visit `https://your-app.up.railway.app/dashboard/login` — enter your PIN to access the dashboard
3. Update `PUBLIC_URL` in Railway variables to your actual domain, then redeploy:
   ```bash
   git commit --allow-empty -m "chore: trigger redeploy after PUBLIC_URL update"
   git push origin master
   ```

## Local development

1. Copy `.env.example` to `.env` and fill in values
2. Create a local Postgres database: `createdb murder_mystery`
3. Activate venv: `source venv/Scripts/activate` (or `venv\Scripts\activate` on Windows CMD)
4. Run: `flask run`
