import os
from datetime import date

import altair as alt  # type: ignore[import-not-found]
import pandas as pd  # type: ignore[import-not-found]
import streamlit as st  # type: ignore[import-not-found]


DATA_FILE = "prof_phrases_history.csv"
SUPABASE_TABLE = "daily_counts"
SUPABASE_REQUESTS_TABLE = "save_requests"

ADMIN_USERNAME = "admin123"
ADMIN_PASSWORD = "password123"

_supabase_client = None


def _get_supabase():
    """Return Supabase client if SUPABASE_URL and SUPABASE_KEY are set, else None."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    try:
        if hasattr(st, "secrets") and st.secrets:
            supabase_config = st.secrets.get("supabase", {})
            url = url or supabase_config.get("url")
            key = key or supabase_config.get("key")
    except Exception:
        pass
    if url and key:
        try:
            from supabase import create_client  # type: ignore[import-not-found]
            _supabase_client = create_client(url, key)
            return _supabase_client
        except Exception:
            pass
    return None


def _normalize_history_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the history DataFrame always has the same schema:
    columns = ['date', 'are_you_with_me', 'thumbs_up'] with date dtype.

    Also handles older CSVs that used the 'week_date' column name.
    """
    if df.empty:
        return pd.DataFrame(
            columns=["date", "are_you_with_me", "thumbs_up"]
        )

    # Backwards compatibility: old column name 'week_date'
    if "week_date" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"week_date": "date"})

    # Keep only the columns we care about, if they exist
    expected_cols = ["date", "are_you_with_me", "thumbs_up"]
    existing_cols = [c for c in expected_cols if c in df.columns]
    df = df[existing_cols]

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    # Reorder / add missing columns
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0
    return df[expected_cols]


def load_history() -> pd.DataFrame:
    """Load historical daily counts from Supabase (if configured) or from CSV."""
    supabase = _get_supabase()
    if supabase is not None:
        try:
            resp = supabase.table(SUPABASE_TABLE).select("*").order("class_date").execute()
            rows = resp.data or []
            if not rows:
                return _normalize_history_df(pd.DataFrame())
            df = pd.DataFrame(rows)
            df = df.rename(columns={"class_date": "date"})
            df["date"] = pd.to_datetime(df["date"]).dt.date
            return _normalize_history_df(df[["date", "are_you_with_me", "thumbs_up"]])
        except Exception:
            return _normalize_history_df(pd.DataFrame())
    if os.path.exists(DATA_FILE):
        raw_df = pd.read_csv(DATA_FILE)
        return _normalize_history_df(raw_df)
    return _normalize_history_df(pd.DataFrame())


def save_daily_counts(class_date: date, are_count: int, thumbs_count: int) -> None:
    """
    Save the counts for a given date.
    Uses Supabase if configured (one row per date; latest save wins). Otherwise uses CSV.
    """
    supabase = _get_supabase()
    if supabase is not None:
        row = {
            "class_date": class_date.isoformat(),
            "are_you_with_me": are_count,
            "thumbs_up": thumbs_count,
        }
        supabase.table(SUPABASE_TABLE).upsert(row, on_conflict="class_date").execute()
        return
    df = load_history()
    new_row = pd.DataFrame(
        {
            "date": [class_date],
            "are_you_with_me": [are_count],
            "thumbs_up": [thumbs_count],
        }
    )
    if not df.empty and "date" in df.columns:
        df = df[df["date"] != class_date]
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)


def submit_save_request(class_date: date, are_count: int, thumbs_count: int) -> bool:
    """Submit a save request (pending approval). Returns True if submitted, False if no Supabase."""
    supabase = _get_supabase()
    if supabase is None:
        return False
    row = {
        "class_date": class_date.isoformat(),
        "are_you_with_me": are_count,
        "thumbs_up": thumbs_count,
        "status": "pending",
    }
    supabase.table(SUPABASE_REQUESTS_TABLE).insert(row).execute()
    return True


def get_pending_requests() -> list[dict]:
    """Return list of pending save requests (each has id, class_date, are_you_with_me, thumbs_up, created_at)."""
    supabase = _get_supabase()
    if supabase is None:
        return []
    try:
        resp = (
            supabase.table(SUPABASE_REQUESTS_TABLE)
            .select("*")
            .eq("status", "pending")
            .order("created_at", desc=True)
            .execute()
        )
        return list(resp.data or [])
    except Exception:
        return []


def approve_request(request_id: str) -> None:
    """Approve a request: add to daily_counts and mark request approved."""
    supabase = _get_supabase()
    if supabase is None:
        return
    resp = (
        supabase.table(SUPABASE_REQUESTS_TABLE)
        .select("class_date, are_you_with_me, thumbs_up")
        .eq("id", request_id)
        .single()
        .execute()
    )
    if not resp.data:
        return
    row = resp.data
    supabase.table(SUPABASE_TABLE).upsert(
        {
            "class_date": row["class_date"],
            "are_you_with_me": row["are_you_with_me"],
            "thumbs_up": row["thumbs_up"],
        },
        on_conflict="class_date",
    ).execute()
    supabase.table(SUPABASE_REQUESTS_TABLE).update({"status": "approved"}).eq("id", request_id).execute()


def reject_request(request_id: str) -> None:
    """Mark a request as rejected."""
    supabase = _get_supabase()
    if supabase is None:
        return
    supabase.table(SUPABASE_REQUESTS_TABLE).update({"status": "rejected"}).eq("id", request_id).execute()


st.set_page_config(page_title="CC6 TRACKER", layout="centered")

# ---------- Global styles ----------

st.markdown(
    """
    <style>
    .counter-number {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* Reset button only: block that contains our anchor, then the next block’s button */
    div:has(.reset-btn-anchor) + div [data-testid="stButton"] button {
        background-color: #ef4444 !important;
        color: white !important;
        border-color: #dc2626 !important;
    }
    div:has(.reset-btn-anchor) + div [data-testid="stButton"] button:hover {
        background-color: #dc2626 !important;
        border-color: #b91c1c !important;
    }

    /* Save button only: green */
    div:has(.save-btn-anchor) + div [data-testid="stButton"] button {
        background-color: #22c55e !important;
        color: white !important;
        border-color: #16a34a !important;
    }
    div:has(.save-btn-anchor) + div [data-testid="stButton"] button:hover {
        background-color: #16a34a !important;
        border-color: #15803d !important;
    }

    /* Pop-emoji animation overlay */
    .pop-emoji-overlay {
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: none;
        z-index: 9999;
    }
    .pop-emoji {
        font-size: 5rem;
        animation: popFade 0.7s ease-out forwards;
    }
    @keyframes popFade {
        0%   { transform: scale(0.3); opacity: 1; }
        40%  { transform: scale(1.4); opacity: 1; }
        100% { transform: scale(1.2); opacity: 0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Initialize admin session state (before top bar uses it) ----------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "admin_show_login" not in st.session_state:
    st.session_state.admin_show_login = False

# ---------- Top bar: title + admin login (top right) ----------

top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.title("CC6 TRACKER")
    st.write(
        "Track how many times the guy says "
        "`ARE YOU WITH ME?` and `THUMBS UP` during class."
    )
with top_col2:
    if st.session_state.is_admin:
        if st.button("Admin (logout)"):
            st.session_state.is_admin = False
            st.rerun()
        st.caption("Logged in as admin")
    else:
        if st.button("Admin login"):
            st.session_state.admin_show_login = not st.session_state.admin_show_login
            st.rerun()
        if st.session_state.admin_show_login:
            with st.form("admin_login_form"):
                un = st.text_input("Username", key="admin_un")
                pw = st.text_input("Password", type="password", key="admin_pw")
                login_clicked = st.form_submit_button("Log in")
                cancel_clicked = st.form_submit_button("Cancel")
                if login_clicked:
                    if un == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
                        st.session_state.is_admin = True
                        st.session_state.admin_show_login = False
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                if cancel_clicked:
                    st.session_state.admin_show_login = False
                    st.rerun()

# ---------- Initialize session state ----------

if "are_count" not in st.session_state:
    st.session_state.are_count = 0
if "thumbs_count" not in st.session_state:
    st.session_state.thumbs_count = 0
if "show_stats" not in st.session_state:
    st.session_state.show_stats = False
if "pop_emoji" not in st.session_state:
    st.session_state.pop_emoji = None
if "pop_emoji_id" not in st.session_state:
    st.session_state.pop_emoji_id = 0


def _set_pop(emoji: str) -> None:
    st.session_state.pop_emoji = emoji
    st.session_state.pop_emoji_id = st.session_state.get("pop_emoji_id", 0) + 1


def are_plus():
    _set_pop("🔥🔥🔥")
    st.session_state.are_count += 1


def are_minus():
    _set_pop("💩💩💩")
    st.session_state.are_count = max(0, st.session_state.are_count - 1)


def thumbs_plus():
    _set_pop("👍👍👍")
    st.session_state.thumbs_count += 1


def thumbs_minus():
    _set_pop("👎👎👎")
    st.session_state.thumbs_count = max(0, st.session_state.thumbs_count - 1)


# ---------- Live counter UI ----------

st.subheader("Live Counter (this class / this date)")

cols = st.columns(3)

with cols[0]:
    st.markdown("**ARE YOU WITH ME?**")
    st.button(
        "WITH YOU🔥🔥🔥    ",
        key="are_plus",
        on_click=are_plus,
    )
    st.markdown(
        f"<div class='counter-number'>{st.session_state.are_count}</div>",
        unsafe_allow_html=True,
    )
    st.button(
        "NOT WITH YOU💩💩💩",
        key="are_minus",
        on_click=are_minus,
    )

with cols[1]:
    st.markdown("**THUMBS UP**")
    st.button(
        "THUMBS UP👍👍👍  ",
        key="thumbs_plus",
        on_click=thumbs_plus,
    )
    st.markdown(
        f"<div class='counter-number'>{st.session_state.thumbs_count}</div>",
        unsafe_allow_html=True,
    )
    st.button(
        "THUMBS DOWN👎👎👎",
        key="thumbs_minus",
        on_click=thumbs_minus,
    )

with cols[2]:
    st.markdown("**Controls**")
    st.markdown('<div class="reset-btn-anchor"></div>', unsafe_allow_html=True)
    if st.button("Reset current counts"):
        st.session_state.are_count = 0
        st.session_state.thumbs_count = 0

# Pop-emoji animation (unique id each time so CSS animation replays)
if st.session_state.pop_emoji:
    uid = st.session_state.pop_emoji_id
    emoji_container = st.empty()
    emoji_container.markdown(
        f'<div class="pop-emoji-overlay" key="{uid}">'
        f'<span class="pop-emoji">{st.session_state.pop_emoji}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    import time
    time.sleep(0.7)  # Match animation duration
    emoji_container.empty()
    st.session_state.pop_emoji = None

st.divider()

# ---------- Daily/class save section ----------

st.subheader("Save this class / date totals")

selected_date = st.date_input("Class date", value=date.today())

st.markdown('<div class="save-btn-anchor"></div>', unsafe_allow_html=True)
if st.button("Save this date to history", type="primary"):
    if st.session_state.are_count == 0 and st.session_state.thumbs_count == 0:
        st.warning("Counts are both zero. Did you mean to save?")
    elif st.session_state.is_admin or _get_supabase() is None:
        save_daily_counts(
            selected_date,
            st.session_state.are_count,
            st.session_state.thumbs_count,
        )
        st.success("Date saved to history (existing entry, if any, was updated).")
        st.session_state.are_count = 0
        st.session_state.thumbs_count = 0
    else:
        if submit_save_request(
            selected_date,
            st.session_state.are_count,
            st.session_state.thumbs_count,
        ):
            st.success("Submitted for approval. The admin will review your counts.")
            st.session_state.are_count = 0
            st.session_state.thumbs_count = 0
        else:
            st.error("Could not submit. Database may not be configured.")

st.divider()

# ---------- Statistics section ----------

st.subheader("Statistics over time")

if st.button("Show / hide statistics"):
    st.session_state.show_stats = not st.session_state.show_stats

if st.session_state.show_stats:
    history_df = load_history()

    view_options = (
        ["Requests", "Line chart", "Bar chart", "Pie chart", "Stats table", "Raw data"]
        if st.session_state.is_admin and _get_supabase() is not None
        else ["Line chart", "Bar chart", "Pie chart", "Stats table", "Raw data"]
    )
    view = st.radio(
        "Choose what to display",
        view_options,
        horizontal=True,
    )

    if view == "Requests":
        pending = get_pending_requests()
        if not pending:
            st.info("No pending requests.")
        else:
            st.write("**Pending save requests (approve or reject):**")
            for r in pending:
                req_id = r["id"]
                class_date = r.get("class_date", "?")
                are_val = r.get("are_you_with_me", 0)
                thumbs_val = r.get("thumbs_up", 0)
                created = r.get("created_at", "")[:19] if r.get("created_at") else ""
                c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                with c1:
                    st.write(f"**Date:** {class_date} — Are you with me: **{are_val}**, Thumbs up: **{thumbs_val}**")
                    if created:
                        st.caption(f"Submitted {created}")
                with c2:
                    if st.button("Approve", key=f"approve_{req_id}"):
                        approve_request(req_id)
                        st.rerun()
                with c3:
                    if st.button("Reject", key=f"reject_{req_id}"):
                        reject_request(req_id)
                        st.rerun()
                st.divider()
    elif history_df.empty:
        st.info("No history yet. Start counting and save a date first.")
    else:
        history_df = history_df.sort_values("date")

        long_df = history_df.melt(
            id_vars=["date"],
            value_vars=["are_you_with_me", "thumbs_up"],
            var_name="counter",
            value_name="count",
        )

        # Green and blue for the two counters (used in line, bar, pie)
        color_scale = alt.Scale(
            domain=["are_you_with_me", "thumbs_up"],
            range=["#22c55e", "#3b82f6"],
        )

        if view == "Raw data":
            st.write("**Raw data (by date):**")
            st.dataframe(history_df, use_container_width=True)

        elif view == "Stats table":
            st.write("**Summary statistics:**")
            st.write(history_df[["are_you_with_me", "thumbs_up"]].describe())

        elif view == "Line chart":
            st.write("**Line chart:**")
            line_chart = (
                alt.Chart(long_df)
                .mark_line(point=True)
                .encode(
                    x="date:T",
                    y="count:Q",
                    color=alt.Color("counter:N", scale=color_scale),
                    tooltip=["date:T", "counter:N", "count:Q"],
                )
                .properties(height=400)
            )
            st.altair_chart(line_chart, use_container_width=True)

        elif view == "Bar chart":
            st.write("**Bar chart (counts per date):**")
            # Use date as ordinal so each date is one band; xOffset gives two bars per date
            bar_df = long_df.copy()
            bar_df["date_str"] = bar_df["date"].astype(str)
            bar_chart = (
                alt.Chart(bar_df)
                .mark_bar()
                .encode(
                    x=alt.X("date_str:N", title="Date", sort=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("count:Q", title="Count"),
                    xOffset="counter:N",
                    color=alt.Color("counter:N", scale=color_scale),
                    tooltip=["date_str:N", "counter:N", "count:Q"],
                )
                .properties(height=400)
            )
            st.altair_chart(bar_chart, use_container_width=True)

        elif view == "Pie chart":
            st.write("**Pie chart (totals across all dates):**")
            totals_df = (
                long_df.groupby("counter", as_index=False)["count"].sum()
            )
            pie_chart = (
                alt.Chart(totals_df)
                .mark_arc()
                .encode(
                    theta="count:Q",
                    color=alt.Color("counter:N", scale=color_scale),
                    tooltip=["counter:N", "count:Q"],
                )
                .properties(height=400)
            )
            st.altair_chart(pie_chart, use_container_width=True)
else:
    st.caption("Press 'Show / hide statistics' to see history and charts.")

