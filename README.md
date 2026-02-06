# Professor Phrase Tracker

Track how many times my professor says **"ARE YOU WITH ME?"** and **"THUMBS UP"** using a simple web app built with Python, Streamlit, and pandas.

## Public link

https://cc6-tracker.streamlit.app/

## Setup

1. Create and activate a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate      # macOS / Linux
   # .\venv\Scripts\activate     # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run the app

From this folder (where `app.py` is located), run:

```bash
streamlit run app.py
```

A browser window will open.

- Use the **"ARE YOU WITH ME?"** and **"THUMBS UP"** buttons during class to count phrases in real time.
- Choose a date and click **"Save this date to history"** to store the totals (persisted in Supabase if configured, otherwise in a local CSV).
- Click **"Show / hide statistics"** to see history, line/bar/pie charts, and summary stats.

## Persistent storage (Supabase)

To keep data permanent (e.g. on Streamlit Cloud), use a free [Supabase](https://supabase.com) database.

1. **Create a Supabase project** at [supabase.com](https://supabase.com) and get your project URL and API key (Settings → API: `Project URL` and `service_role` or `anon` key).

2. **Create the table** in the Supabase SQL Editor (Dashboard → SQL Editor). Run:

   ```sql
   create table if not exists daily_counts (
     class_date date primary key,
     are_you_with_me int not null default 0,
     thumbs_up int not null default 0
   );

   create table if not exists save_requests (
     id uuid primary key default gen_random_uuid(),
     class_date date not null,
     are_you_with_me int not null default 0,
     thumbs_up int not null default 0,
     status text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
     created_at timestamptz not null default now()
   );

   alter table daily_counts enable row level security;
   alter table save_requests enable row level security;

   create policy "Allow all for service role" on daily_counts for all using (true) with check (true);
   create policy "Allow all for service role" on save_requests for all using (true) with check (true);
   ```

   (If you use the `anon` key instead of `service_role`, adjust the policies so your app can read/write, or disable RLS for these tables if it’s a personal app.)

3. **Configure secrets** so the app can connect:

   - **Streamlit Cloud:** App → Settings → Secrets. Add:
     ```toml
     [supabase]
     url = "https://YOUR_PROJECT_REF.supabase.co"
     key = "YOUR_SERVICE_ROLE_OR_ANON_KEY"
     ```
   - **Local:** Create `.streamlit/secrets.toml` (same format as above). Do not commit this file.

   Alternatively you can set environment variables `SUPABASE_URL` and `SUPABASE_KEY` instead of secrets.

If Supabase is not configured, the app falls back to saving and loading from `prof_phrases_history.csv` (fine for local use; data is lost on Streamlit Cloud restarts).

**Admin approval:** When Supabase is configured, non-admin users’ saves are submitted for approval. Log in via **Admin login** (top right) with username `admin123` and password `password123`. The admin sees the same page plus a **Requests** tab under statistics to approve or reject pending counts.

