# CC6 Tracker (React)

A React + Vite version of the CC6 Tracker app, deployable to GitHub Pages.

## Local development

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173

## Build

```bash
npm run build
```

Output goes to `dist/`.

## Deploy to GitHub Pages

1. **Enable GitHub Pages** in your repo: Settings → Pages → Source: GitHub Actions.

2. **Add Supabase secrets** (optional): Settings → Secrets and variables → Actions:
   - `VITE_SUPABASE_URL` – your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` – your Supabase anon key

3. **Configure base path** if your repo name differs from `cc6-tracker`: edit `.github/workflows/deploy-pages.yml` and set `VITE_BASE_PATH` to `"/your-repo-name/"`.

4. Push to `main` – the workflow will build and deploy.

Without Supabase, the app uses `localStorage` for persistence (data stays in the browser only).
