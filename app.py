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
"""Study Office Decision Support: who may need a conversation, and what a contact rule gets right and wrong."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from portable import Model

URL = "https://raw.githubusercontent.com/aaubs/ds-master/main/assignments/study-office/data/"
TOP_N = 40
LABEL = {
    "age": "Age", "admission_grade": "Admission grade", "international": "International student",
    "first_gen": "First-generation student", "su_scholarship": "SU scholarship", "fees_owed": "Fees owed",
    "moved_from_home": "Moved from home", "married": "Married", "evening_programme": "Evening programme",
    "logins_total": "Total logins", "logins_last3": "Logins in the last 3 weeks",
    "logins_trend": "Change in login activity", "submitted_share": "Share of assignments submitted",
    "missed_last3": "Missed activities in the last 3 weeks", "quiz_mean": "Average quiz score",
    "weeks_since_login": "Weeks since last login", "programme": "Programme", "gender": "Gender",
}

st.set_page_config(page_title="Study Office Decision Support", layout="wide")


@st.cache_resource
def load_model():
    return Model(Path(__file__).parent / "model")


@st.cache_data
def load_data():
    return pd.read_csv(URL + "history_week6.csv"), pd.read_csv(URL + "new_week6.csv")


def four_boxes(d):
    """The four outcomes, precision and recall. d needs a 'left' column (1 = left) and a 'contacted' column (True/False)."""
    left, c = d["left"] == 1, d["contacted"]
    reached, worried, missed, stayed = (c & left).sum(
    ), (c & ~left).sum(), (~c & left).sum(), (~c & ~left).sum()
    precision = reached / (reached + worried) if reached + worried else 0
    recall = reached / (reached + missed) if reached + missed else 0
    return int(reached), int(worried), int(missed), int(stayed), precision, recall


model = load_model()
history, new = load_data()

# 2026 students (this week), ranked by risk; the first 40 are the suggested outreach list
new["risk"] = model.predict_proba(new)
new = new.sort_values("risk", ascending=False).reset_index(drop=True)
new["Estimated risk"] = new["risk"] * 100
new["Priority"] = np.where(new.index < TOP_N, f"Top {TOP_N}", "")
new["Fees owed"] = new["fees_owed"].map({1: "Yes", 0: "No"})
new["SU scholarship"] = new["su_scholarship"].map({1: "Yes", 0: "No"})

# 2025 students, ranked by risk, to test the rule on people whose outcome we know
past = history[history["cohort"] == 2025].copy()
past["risk"] = model.predict_proba(past)
past = past.sort_values("risk", ascending=False)

st.title("Study Office Decision Support")
st.caption("A risk score is a prompt to check in, not a judgement about a student.")
tab_list, tab_rule, tab_why = st.tabs(
    ["This week's list", "Mistakes of a rule", "Why this student?"])

# ---------------------------------------------------------------- 1. this week's list
with tab_list:
    st.write(f"The {len(new)} new students, from highest to lowest estimated risk. "
             f"The first {TOP_N} are the suggested outreach list.")
    st.dataframe(
        new[["Priority", "student_id", "Estimated risk",
            "programme", "Fees owed", "SU scholarship"]],
        hide_index=True, width="stretch", height=600,
        column_config={
            "student_id": "Student", "programme": "Programme",
            "Estimated risk": st.column_config.ProgressColumn("Estimated risk", min_value=0, max_value=100, format="%.0f%%"),
        },
    )

# ---------------------------------------------------------------- 2 + 3. mistakes of a rule, per group
with tab_rule:
    st.write("Rule: contact the students with the highest estimated risk. "
             "We test it on the 2025 students, where we already know who left.")
    n = st.slider("How many conversations can the office have?",
                  0, len(past), TOP_N)
    past["contacted"] = np.arange(len(past)) < n
    reached, worried, missed, stayed, precision, recall = four_boxes(past)

    st.markdown(
        f"### {reached} reached in time, {worried} worried for nothing, {missed} missed")
    cols = st.columns(4)
    cols[0].metric("Reached in time", reached,
                   help="Contacted, and later left.")
    cols[1].metric("Worried for nothing", worried,
                   help="Contacted, but stayed.")
    cols[2].metric("Missed", missed, help="Not contacted, but later left.")
    cols[3].metric("Stayed, no outreach needed", stayed,
                   help="Not contacted, and stayed.")
    st.write(
        f"**Precision {precision:.0%}**: of the {n} students contacted, {precision:.0%} later left.")
    st.write(
        f"**Recall {recall:.0%}**: of the {reached + missed} students who left, {recall:.0%} were contacted.")
    st.caption(
        "This looks backwards: it cannot tell us whether a conversation would have changed anyone's mind.")

    st.markdown("### The same, per group")
    rows = []
    for name, group in (("Domestic", past[past["international"] == 0]), ("International", past[past["international"] == 1])):
        a, b, c, d, p, r = four_boxes(group)
        rows.append({"Group": name, "Students": len(group), "Reached in time": a, "Worried for nothing": b,
                     "Missed": c, "Stayed, no outreach needed": d, "Precision": f"{p:.0%}", "Recall": f"{r:.0%}"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ---------------------------------------------------------------- 4. why is a student on the list?
with tab_why:
    st.write("Pick a student to see what moves their estimated risk. These are model signals, not facts about the student.")
    student = st.selectbox("Student (highest risk first)", new["student_id"])
    row = new[new["student_id"] == student]
    effect = model.contributions(row).iloc[0]
    strongest = effect.reindex(
        effect.abs().sort_values(ascending=False).index).head(6)

    st.metric("Estimated risk", f"{row['risk'].iloc[0]:.0%}")
    raising = [f"{LABEL[f]} ({row[f].iloc[0]})" for f in effect[effect > 0].sort_values(
        ascending=False).head(3).index]
    st.write("**Pushing the risk up:** " +
             (" · ".join(raising) if raising else "nothing stands out"))
    st.bar_chart(strongest.rename(index=LABEL), horizontal=True)
    st.caption(
        "Bars to the right raise the estimated risk, bars to the left lower it.")
