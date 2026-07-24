# Miru Allergen Matrix

A staff-facing search engine for the Miru allergen matrix. Select any
combination of menu items and allergens to produce an instant cross-reference
grid — color-coded by severity (Contains / MOD / CC / Via Ingredient).

## Deploy to Railway

### One-click (recommended)

1. Push this repo to GitHub (or any Git host).
2. In Railway: **New Project → Deploy from GitHub repo** → select this repo.
3. Railway auto-detects Python via Nixpacks and runs `gunicorn` from `Procfile`.
4. No environment variables required. The app binds to `$PORT` automatically.

### Railway CLI

```bash
npm i -g @railway/cli
railway login
railway init          # inside this directory
railway up
```

## Local dev

```bash
pip install -r requirements.txt
python app.py         # → http://localhost:5000
```

## Updating the allergen matrix

Replace `data/Miru_Allergen_Matrix_6_29_26.xlsx` with the new file and update
the filename reference in `app.py` (the `_data_path` variable near the bottom
of the imports section). Redeploy — the app re-parses the sheet on startup.

## Cell badge legend

| Badge      | Meaning                                              |
|------------|------------------------------------------------------|
| `—`        | Allergen not present in this dish                    |
| `✕ X`      | Allergen present — cannot be removed                 |
| `MOD`      | Allergen present but dish can be modified to remove  |
| `CC`       | Cross-contamination risk (e.g. shared fryer)         |
| *text*     | Allergen present via a specific ingredient (e.g. "Mayo", "7 Spice") |
