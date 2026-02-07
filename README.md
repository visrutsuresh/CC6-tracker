# Professor Phrase Tracker (CC6 Tracker)

Track how many times my professor says **"ARE YOU WITH ME?"** and **"THUMBS UP"** using a React web app (Vite + Supabase or localStorage).

## Run locally

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173

## Deploy (GitHub Pages)

See [web/README.md](web/README.md) for build and GitHub Actions deploy steps.

## Supabase (optional)

To persist data, create a [Supabase](https://supabase.com) project and add your URL and anon key. Use `web/.env.example` as a template (copy to `web/.env` and fill in values). Without Supabase, the app uses `localStorage` (browser-only).
