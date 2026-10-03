# import pandas as pd
# import streamlit as st
# import portable


# st.set_page_config(page_title="Study Office Decision Support", layout="wide")
# st.title("Study Office Decision Support")
# st.caption(
#     "A practical guide to who may need outreach. A risk score is a prompt to check in, "
#     "not a judgement about a student."
# )

# BASE_URL = (
#     "https://raw.githubusercontent.com/aaubs/ds-master/main/assignments/"
#     "study-office/data/"
# )
# OUTCOME_LABELS = {
#     "reached": "Reached in time",
#     "false_alarm": "Worried for nothing",
#     "missed": "Missed",
#     "not_at_risk": "Stayed enrolled; no outreach needed",
# }
# FEATURE_LABELS = {
#     "age": "Age",
#     "admission_grade": "Admission grade",
#     "international": "International student",
#     "first_gen": "First-generation student",
#     "su_scholarship": "SU scholarship",
#     "fees_owed": "Fees owed",
#     "moved_from_home": "Moved from home",
#     "married": "Married",
#     "evening_programme": "Evening programme",
#     "logins_total": "Total logins",
#     "logins_last3": "Logins in the last three weeks",
#     "logins_trend": "Change in login activity",
#     "submitted_share": "Share of assignments submitted",
#     "missed_last3": "Missed activities in the last three weeks",
#     "quiz_mean": "Average quiz score",
#     "weeks_since_login": "Weeks since last login",
#     "programme": "Programme",
#     "gender": "Gender",
# }


# @st.cache_resource
# def load_model():
#     return portable.Model("model")


# @st.cache_data
# def load_data():
#     history = pd.read_csv(BASE_URL + "history_week6.csv")
#     new_students = pd.read_csv(BASE_URL + "new_week6.csv")
#     return history, new_students


# def outcomes_for_selection(data, selected):
#     actual_left = data["left"].astype(int).eq(1)
#     reached = int((selected & actual_left).sum())
#     false_alarm = int((selected & ~actual_left).sum())
#     missed = int((~selected & actual_left).sum())
#     not_at_risk = int((~selected & ~actual_left).sum())
#     precision = reached / \
#         (reached + false_alarm) if reached + false_alarm else None
#     recall = reached / (reached + missed) if reached + missed else None
#     return {
#         "reached": reached,
#         "false_alarm": false_alarm,
#         "missed": missed,
#         "not_at_risk": not_at_risk,
#         "precision": precision,
#         "recall": recall,
#     }


# def show_outcome_cards(metrics):
#     cards = st.columns(4)
#     for card, key in zip(cards, OUTCOME_LABELS):
#         card.metric(OUTCOME_LABELS[key], metrics[key])


# def format_rate(value):
#     return "Not applicable" if value is None else f"{value:.1%}"


# model = load_model()
# history, new_students = load_data()

# required_history_columns = {"cohort", "international", "left"}
# missing_columns = required_history_columns.difference(history.columns)
# if missing_columns:
#     st.error(
#         "The historical data is missing required columns: "
#         + ", ".join(sorted(missing_columns))
#     )
#     st.stop()

# history_2025 = history.loc[history["cohort"].eq(2025)].copy()
# if history_2025.empty:
#     st.error("The historical data does not contain a 2025 cohort.")
#     st.stop()

# history_2025["risk"] = model.predict_proba(history_2025)
# new_students["risk"] = model.predict_proba(new_students)
# new_students = new_students.sort_values(
#     "risk", ascending=False, kind="mergesort"
# ).reset_index(drop=True)
# new_students["Estimated risk (%)"] = new_students["risk"] * 100
# new_students["SU scholarship"] = (
#     new_students["su_scholarship"].map({1: "Yes", 0: "No"}).fillna("Unknown")
# )
# new_students["Outreach priority"] = [
#     "Top 40" if rank < 40 else "" for rank in range(len(new_students))
# ]

# st.header("This week's list")
# st.write(
#     "Students are ranked from highest to lowest estimated risk. "
#     "The first 40 are marked as the suggested outreach list."
# )

# list_columns = [
#     "Outreach priority",
#     "student_id",
#     "Estimated risk (%)",
#     "programme",
#     "fees_owed",
#     "SU scholarship",
# ]
# st.dataframe(
#     new_students[list_columns],
#     hide_index=True,
#     width="stretch",
#     height=520,
#     column_config={
#         "Estimated risk (%)": st.column_config.NumberColumn(
#             "Estimated risk", format="%.1f%%"
#         ),
#         "fees_owed": st.column_config.NumberColumn("Fees owed", format="%d"),
#     },
# )

# st.header("What happens if we contact this many students?")
# st.caption(
#     "We replay the policy on the 2025 cohort: the model ranks those students, "
#     "then selects the highest-risk students up to the chosen contact capacity."
# )
# contact_count = st.slider(
#     "Number of conversations the office can have",
#     min_value=0,
#     max_value=len(history_2025),
#     value=min(40, len(history_2025)),
#     step=1,
# )

# selected_2025 = pd.Series(False, index=history_2025.index)
# selected_indices = history_2025["risk"].sort_values(
#     ascending=False, kind="mergesort"
# ).head(contact_count).index
# selected_2025.loc[selected_indices] = True
# overall = outcomes_for_selection(history_2025, selected_2025)

# st.subheader("2025 cohort: the four outcomes")
# st.caption(
#     "This is a retrospective comparison: it shows who the policy would contact "
#     "and who later left. It cannot tell us whether outreach would have changed "
#     "any student's outcome."
# )
# show_outcome_cards(overall)
# precision_col, recall_col = st.columns(2)
# precision_col.metric(
#     "Precision",
#     format_rate(overall["precision"]),
#     help="Of the students contacted, the share who later left.",
# )
# recall_col.metric(
#     "Recall",
#     format_rate(overall["recall"]),
#     help="Of the students who later left, the share contacted.",
# )

# st.subheader("Same results by student group")
# group_rows = []
# for label, group_value in (("Domestic", 0), ("International", 1)):
#     group = history_2025.loc[history_2025["international"].astype(
#         int).eq(group_value)]
#     group_selection = selected_2025.loc[group.index]
#     metrics = outcomes_for_selection(group, group_selection)
#     group_rows.append(
#         {
#             "Group": label,
#             "Students": len(group),
#             OUTCOME_LABELS["reached"]: metrics["reached"],
#             OUTCOME_LABELS["false_alarm"]: metrics["false_alarm"],
#             OUTCOME_LABELS["missed"]: metrics["missed"],
#             OUTCOME_LABELS["not_at_risk"]: metrics["not_at_risk"],
#             "Precision (%)": (
#                 metrics["precision"] * 100
#                 if metrics["precision"] is not None
#                 else None
#             ),
#             "Recall (%)": (
#                 metrics["recall"] *
#                 100 if metrics["recall"] is not None else None
#             ),
#         }
#     )
# st.dataframe(
#     pd.DataFrame(group_rows),
#     hide_index=True,
#     width="stretch",
#     column_config={
#         "Precision (%)": st.column_config.NumberColumn(
#             "Precision", format="%.1f%%"
#         ),
#         "Recall (%)": st.column_config.NumberColumn("Recall", format="%.1f%%"),
#     },
# )

# st.header("Why is a student on the list?")
# st.caption(
#     "Select a student to see the strongest factors pushing their estimated risk up. "
#     "These are model signals, not proof of a student's circumstances."
# )
# student_id = st.selectbox(
#     "Choose a student",
#     new_students["student_id"].tolist(),
# )
# selected_student_index = new_students.index[
#     new_students["student_id"].eq(student_id)
# ][0]
# contributions = model.contributions(new_students.loc[[selected_student_index]])
# student_contributions = contributions.iloc[0].sort_values(ascending=False)
# positive_contributions = student_contributions.loc[student_contributions > 0].head(
#     3)

# student_row = new_students.loc[selected_student_index]
# st.write(
#     f"**{student_id}** — estimated risk: **{student_row['risk']:.1%}**. "
#     + (
#         "Factors most strongly increasing the model's risk estimate:"
#         if not positive_contributions.empty
#         else "No individual factor increased this student's estimate relative to the model baseline."
#     )
# )
# if not positive_contributions.empty:
#     explanation = pd.DataFrame(
#         {
#             "Factor": [
#                 FEATURE_LABELS.get(name, name.replace("_", " ").capitalize())
#                 for name in positive_contributions.index
#             ],
#             "Student's data": [
#                 str(student_row[name]) for name in positive_contributions.index
#             ],
#             "Contribution to risk": positive_contributions.values,
#         }
#     )
#     st.dataframe(
#         explanation,
#         hide_index=True,
#         width="stretch",
#         column_config={
#             "Contribution to risk": st.column_config.NumberColumn(
#                 "Contribution to risk", format="%.3f"
#             )
#         },
#     )
import altair as alt
import pandas as pd
import streamlit as st
import portable

st.set_page_config(
    page_title="Study Office Decision Support", page_icon="🎓", layout="wide"
)

BASE_URL = (
    "https://raw.githubusercontent.com/aaubs/ds-master/main/assignments/"
    "study-office/data/"
)
OUTREACH_SIZE = 40
RAISES, LOWERS = "Raises risk", "Lowers risk"
RAISES_COLOUR, LOWERS_COLOUR = "#B5473F", "#1F6F78"

OUTCOME_LABELS = {
    "reached": "Reached in time",
    "false_alarm": "Worried for nothing",
    "missed": "Missed",
    "not_at_risk": "Stayed enrolled; no outreach needed",
}
OUTCOME_HELP = {
    "reached": "Contacted, and the student later left.",
    "false_alarm": "Contacted, but the student stayed.",
    "missed": "Not contacted, and the student later left.",
    "not_at_risk": "Not contacted, and the student stayed.",
}
FEATURE_LABELS = {
    "age": "Age",
    "admission_grade": "Admission grade",
    "international": "International student",
    "first_gen": "First-generation student",
    "su_scholarship": "SU scholarship",
    "fees_owed": "Fees owed",
    "moved_from_home": "Moved from home",
    "married": "Married",
    "evening_programme": "Evening programme",
    "logins_total": "Total logins",
    "logins_last3": "Logins in the last three weeks",
    "logins_trend": "Change in login activity",
    "submitted_share": "Share of assignments submitted",
    "missed_last3": "Missed activities in the last three weeks",
    "quiz_mean": "Average quiz score",
    "weeks_since_login": "Weeks since last login",
    "programme": "Programme",
    "gender": "Gender",
}
YES_NO_FEATURES = {
    "international", "first_gen", "su_scholarship", "fees_owed",
    "moved_from_home", "married", "evening_programme",
}


@st.cache_resource
def load_model():
    return portable.Model("model")


@st.cache_data
def load_data():
    history = pd.read_csv(BASE_URL + "history_week6.csv")
    new_students = pd.read_csv(BASE_URL + "new_week6.csv")
    return history, new_students


def outcomes_for_selection(data, selected):
    actual_left = data["left"].astype(int).eq(1)
    reached = int((selected & actual_left).sum())
    false_alarm = int((selected & ~actual_left).sum())
    missed = int((~selected & actual_left).sum())
    not_at_risk = int((~selected & ~actual_left).sum())
    precision = reached / \
        (reached + false_alarm) if reached + false_alarm else None
    recall = reached / (reached + missed) if reached + missed else None
    return {
        "reached": reached,
        "false_alarm": false_alarm,
        "missed": missed,
        "not_at_risk": not_at_risk,
        "precision": precision,
        "recall": recall,
    }


def format_rate(value):
    return "Not applicable" if value is None else f"{value:.1%}"


def yes_no(series):
    return series.map({1: "Yes", 0: "No"}).fillna("Unknown")


def format_value(name, value):
    if pd.isna(value):
        return "Missing"
    if name in YES_NO_FEATURES:
        return "Yes" if int(value) == 1 else "No"
    if name == "submitted_share":
        return f"{float(value):.0%}"
    if isinstance(value, str):
        return value
    return f"{float(value):.2f}".rstrip("0").rstrip(".")


def show_outcome_grid(metrics):
    """2x2 grid: rows are who we contacted, columns are what happened."""
    label_col, left_col, stayed_col = st.columns([0.8, 2, 2])
    left_col.markdown("**Student later left**")
    stayed_col.markdown("**Student stayed**")
    rows = (
        ("Contacted", "reached", "false_alarm"),
        ("Not contacted", "missed", "not_at_risk"),
    )
    for row_label, left_key, stayed_key in rows:
        label_col, left_col, stayed_col = st.columns([0.8, 2, 2])
        label_col.markdown(f"<br>**{row_label}**", unsafe_allow_html=True)
        for col, key in ((left_col, left_key), (stayed_col, stayed_key)):
            with col.container(border=True):
                st.metric(
                    OUTCOME_LABELS[key], metrics[key], help=OUTCOME_HELP[key]
                )


model = load_model()
history, new_students = load_data()

required_history_columns = {"cohort", "international", "left"}
missing_columns = required_history_columns.difference(history.columns)
if missing_columns:
    st.error(
        "The historical data is missing required columns: "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()

history_2025 = history.loc[history["cohort"].eq(2025)].copy()
if history_2025.empty:
    st.error("The historical data does not contain a 2025 cohort.")
    st.stop()

history_2025["risk"] = model.predict_proba(history_2025)
new_students["risk"] = model.predict_proba(new_students)
new_students = new_students.sort_values(
    "risk", ascending=False, kind="mergesort"
).reset_index(drop=True)
new_students["Estimated risk (%)"] = new_students["risk"] * 100
new_students["SU scholarship"] = yes_no(new_students["su_scholarship"])
new_students["Fees owed"] = yes_no(new_students["fees_owed"])
new_students["Suggested for outreach"] = new_students.index < OUTREACH_SIZE

# ---------- Header ----------
st.title("Study Office Decision Support")
st.caption(
    "A practical guide to who may need outreach. A risk score is a prompt to "
    "check in, not a judgement about a student."
)

total_new = len(new_students)
top_risk = new_students["risk"].iloc[0]
cutoff_risk = new_students["risk"].iloc[min(OUTREACH_SIZE, total_new) - 1]
m1, m2, m3 = st.columns(3)
m1.metric("Students this week", total_new)
m2.metric("Suggested for outreach", min(OUTREACH_SIZE, total_new))
m3.metric(
    "Risk range on the list",
    f"{cutoff_risk:.0%} to {top_risk:.0%}",
    help="Estimated risk of the last and the first student on the suggested list.",
)

tab_list, tab_whatif, tab_why = st.tabs(
    ["This week's list", "What if we contact more?", "Why this student?"]
)

# ---------- Tab 1: this week's list ----------
with tab_list:
    st.markdown(
        f"Students are ranked from highest to lowest estimated risk. "
        f"The first {OUTREACH_SIZE} are the suggested outreach list."
    )
    list_view = new_students[
        [
            "Suggested for outreach",
            "student_id",
            "Estimated risk (%)",
            "programme",
            "Fees owed",
            "SU scholarship",
        ]
    ]
    only_suggested = st.toggle("Show only the suggested list", value=False)
    if only_suggested:
        list_view = list_view.head(OUTREACH_SIZE)
    st.dataframe(
        list_view,
        hide_index=True,
        width="stretch",
        height=640,
        column_config={
            "Suggested for outreach": st.column_config.CheckboxColumn(
                "Suggested", width="small"
            ),
            "student_id": st.column_config.TextColumn("Student"),
            "Estimated risk (%)": st.column_config.ProgressColumn(
                "Estimated risk",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "programme": st.column_config.TextColumn("Programme"),
        },
    )
    st.download_button(
        "Download suggested list (CSV)",
        new_students.head(OUTREACH_SIZE)[
            ["student_id", "Estimated risk (%)", "programme",
             "Fees owed", "SU scholarship"]
        ].to_csv(index=False),
        file_name="outreach_list.csv",
        mime="text/csv",
    )

# ---------- Tab 2: what if ----------
with tab_whatif:
    st.markdown(
        "We replay the policy on the 2025 cohort: the model ranks those "
        "students, then selects the highest-risk students up to the chosen "
        "contact capacity."
    )
    with st.container(border=True):
        contact_count = st.slider(
            "Number of conversations the office can have",
            min_value=0,
            max_value=len(history_2025),
            value=min(OUTREACH_SIZE, len(history_2025)),
            step=1,
        )
        st.caption(
            f"Contacting the {contact_count} highest-risk students out of "
            f"{len(history_2025)} in the 2025 cohort."
        )

    selected_2025 = pd.Series(False, index=history_2025.index)
    selected_indices = history_2025["risk"].sort_values(
        ascending=False, kind="mergesort"
    ).head(contact_count).index
    selected_2025.loc[selected_indices] = True
    overall = outcomes_for_selection(history_2025, selected_2025)

    st.subheader("2025 cohort: the four outcomes")
    st.caption(
        "This is a retrospective comparison: it shows who the policy would "
        "contact and who later left. It cannot tell us whether outreach would "
        "have changed any student's outcome."
    )
    grid_col, rates_col = st.columns([3, 1.2])
    with grid_col:
        show_outcome_grid(overall)
    with rates_col:
        with st.container(border=True):
            st.metric(
                "Precision",
                format_rate(overall["precision"]),
                help="Of the students contacted, the share who later left.",
            )
        with st.container(border=True):
            st.metric(
                "Recall",
                format_rate(overall["recall"]),
                help="Of the students who later left, the share contacted.",
            )

    st.subheader("Same results by student group")
    group_rows = []
    for label, group_value in (("Domestic", 0), ("International", 1)):
        group = history_2025.loc[
            history_2025["international"].astype(int).eq(group_value)
        ]
        group_selection = selected_2025.loc[group.index]
        metrics = outcomes_for_selection(group, group_selection)
        group_rows.append(
            {
                "Group": label,
                "Students": len(group),
                OUTCOME_LABELS["reached"]: metrics["reached"],
                OUTCOME_LABELS["false_alarm"]: metrics["false_alarm"],
                OUTCOME_LABELS["missed"]: metrics["missed"],
                OUTCOME_LABELS["not_at_risk"]: metrics["not_at_risk"],
                "Precision (%)": (
                    metrics["precision"] * 100
                    if metrics["precision"] is not None
                    else None
                ),
                "Recall (%)": (
                    metrics["recall"] * 100
                    if metrics["recall"] is not None
                    else None
                ),
            }
        )
    st.dataframe(
        pd.DataFrame(group_rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Precision (%)": st.column_config.NumberColumn(
                "Precision", format="%.1f%%"
            ),
            "Recall (%)": st.column_config.NumberColumn(
                "Recall", format="%.1f%%"
            ),
        },
    )

# ---------- Tab 3: why this student ----------
with tab_why:
    st.markdown(
        "Select a student to see what pushes their estimated risk up or down. "
        "These are model signals, not proof of a student's circumstances."
    )
    student_id = st.selectbox(
        "Choose a student (highest risk first)",
        new_students["student_id"].tolist(),
    )
    selected_student_index = new_students.index[
        new_students["student_id"].eq(student_id)
    ][0]
    student_row = new_students.loc[selected_student_index]
    contributions = model.contributions(
        new_students.loc[[selected_student_index]]
    )
    student_contributions = contributions.iloc[0].sort_values(ascending=False)
    raising = student_contributions.loc[student_contributions > 0].head(4)
    lowering = student_contributions.loc[student_contributions < 0].tail(3)
    shown = pd.concat([raising, lowering])

    top_col, info_col = st.columns([1, 3])
    with top_col:
        with st.container(border=True):
            st.metric("Estimated risk", f"{student_row['risk']:.1%}")
    with info_col:
        st.markdown(
            f"**{student_id}** · {student_row['programme']}"
            + (" · on the suggested list" if selected_student_index <
               OUTREACH_SIZE else "")
        )
        if raising.empty:
            st.write(
                "No individual factor increased this student's estimate "
                "relative to the model baseline."
            )
        else:
            st.write(
                "The bars show how strongly each factor moves the model's "
                "estimate. Longer bars mean a bigger push."
            )

    if not shown.empty:
        explanation = pd.DataFrame(
            {
                "Factor": [
                    FEATURE_LABELS.get(n, n.replace("_", " ").capitalize())
                    for n in shown.index
                ],
                "Student's data": [
                    format_value(n, student_row[n]) for n in shown.index
                ],
                "Contribution": shown.values,
                "Effect": [RAISES if v > 0 else LOWERS for v in shown.values],
            }
        )
        chart = (
            alt.Chart(explanation)
            .mark_bar()
            .encode(
                x=alt.X("Contribution:Q", title="Effect on estimated risk"),
                y=alt.Y("Factor:N", sort=None, title=None),
                color=alt.Color(
                    "Effect:N",
                    scale=alt.Scale(
                        domain=[RAISES, LOWERS],
                        range=[RAISES_COLOUR, LOWERS_COLOUR],
                    ),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
                tooltip=["Factor", "Student's data", "Effect",
                         alt.Tooltip("Contribution:Q", format=".2f")],
            )
            .properties(height=40 * len(explanation) + 50)
        )
        chart_col, table_col = st.columns([3, 2])
        with chart_col:
            st.altair_chart(chart, width="stretch")
        with table_col:
            st.dataframe(
                explanation[["Factor", "Student's data"]],
                hide_index=True,
                width="stretch",
            )
