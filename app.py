import os
from datetime import date

import altair as alt  # type: ignore[import-not-found]
import pandas as pd  # type: ignore[import-not-found]
import streamlit as st  # type: ignore[import-not-found]


DATA_FILE = "prof_phrases_history.csv"


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
    """Load historical daily counts from CSV, if it exists."""
    if os.path.exists(DATA_FILE):
        raw_df = pd.read_csv(DATA_FILE)
        return _normalize_history_df(raw_df)
    else:
        return _normalize_history_df(pd.DataFrame())


def save_daily_counts(class_date: date, are_count: int, thumbs_count: int) -> None:
    """
    Save the counts for a given date.

    The 'date' column acts as a primary key:
    - If a row for this date already exists, it is overwritten.
    - Otherwise a new row is added.
    """
    df = load_history()
    new_row = pd.DataFrame(
        {
            "date": [class_date],
            "are_you_with_me": [are_count],
            "thumbs_up": [thumbs_count],
        }
    )

    # Enforce uniqueness on the date column by dropping any existing rows
    if not df.empty and "date" in df.columns:
        df = df[df["date"] != class_date]

    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)


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

st.title("CC6 TRACKER")

st.write(
    "Track how many times the guy says "
    "`ARE YOU WITH ME?` and `THUMBS UP` during class."
)

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
    st.markdown(
        f'<div class="pop-emoji-overlay" id="pop-emoji-{uid}">'
        f'<span class="pop-emoji">{st.session_state.pop_emoji}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.session_state.pop_emoji = None

st.divider()

# ---------- Daily/class save section ----------

st.subheader("Save this class / date totals")

selected_date = st.date_input("Class date", value=date.today())

st.markdown('<div class="save-btn-anchor"></div>', unsafe_allow_html=True)
if st.button("Save this date to history", type="primary"):
    if st.session_state.are_count == 0 and st.session_state.thumbs_count == 0:
        st.warning("Counts are both zero. Did you mean to save?")
    save_daily_counts(
        selected_date,
        st.session_state.are_count,
        st.session_state.thumbs_count,
    )
    st.success("Date saved to history (existing entry, if any, was updated).")
    # Optionally reset after saving
    st.session_state.are_count = 0
    st.session_state.thumbs_count = 0

st.divider()

# ---------- Statistics section ----------

st.subheader("Statistics over time")

if st.button("Show / hide statistics"):
    st.session_state.show_stats = not st.session_state.show_stats

if st.session_state.show_stats:
    history_df = load_history()

    if history_df.empty:
        st.info("No history yet. Start counting and save a date first.")
    else:
        history_df = history_df.sort_values("date")

        view = st.radio(
            "Choose what to display",
            [
                "Line chart",
                "Bar chart",
                "Pie chart",
                "Stats table",
                "Raw data",
            ],
            horizontal=True,
        )

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

