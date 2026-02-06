# Professor Phrase Tracker

Track how many times my professor says **"ARE YOU WITH ME?"** and **"THUMBS UP"** using a simple web app built with Python, Streamlit, and pandas.

## Public lnk

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
- At the end of the week, choose a date and click **"Save this week to history"** to store the totals in `prof_phrases_history.csv`.
- Click **"Show statistics"** to see your weekly history, line charts, and basic summary stats.

