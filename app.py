
# """Study Office Decision Support: who may need a conversation, and what a contact rule gets right and wrong."""
# from pathlib import Path

# import numpy as np
# import pandas as pd
# import streamlit as st
# from portable import Model

# URL = "https://raw.githubusercontent.com/aaubs/ds-master/main/assignments/study-office/data/"
# TOP_N = 40
# LABEL = {
#     "age": "Age", "admission_grade": "Admission grade", "international": "International student",
#     "first_gen": "First-generation student", "su_scholarship": "SU scholarship", "fees_owed": "Fees owed",
#     "moved_from_home": "Moved from home", "married": "Married", "evening_programme": "Evening programme",
#     "logins_total": "Total logins", "logins_last3": "Logins in the last 3 weeks",
#     "logins_trend": "Change in login activity", "submitted_share": "Share of assignments submitted",
#     "missed_last3": "Missed activities in the last 3 weeks", "quiz_mean": "Average quiz score",
#     "weeks_since_login": "Weeks since last login", "programme": "Programme", "gender": "Gender",
# }

# st.set_page_config(page_title="Study Office Decision Support", layout="wide")


# @st.cache_resource
# def load_model():
#     return Model(Path(__file__).parent / "model")


# @st.cache_data
# def load_data():
#     return pd.read_csv(URL + "history_week6.csv"), pd.read_csv(URL + "new_week6.csv")


# def four_boxes(d):
#     """The four outcomes, precision and recall. d needs a 'left' column (1 = left) and a 'contacted' column (True/False)."""
#     left, c = d["left"] == 1, d["contacted"]
#     reached, worried, missed, stayed = (c & left).sum(
#     ), (c & ~left).sum(), (~c & left).sum(), (~c & ~left).sum()
#     precision = reached / (reached + worried) if reached + worried else 0
#     recall = reached / (reached + missed) if reached + missed else 0
#     return int(reached), int(worried), int(missed), int(stayed), precision, recall


# model = load_model()
# history, new = load_data()

# # 2026 students (this week), ranked by risk; the first 40 are the suggested outreach list
# new["risk"] = model.predict_proba(new)
# new = new.sort_values("risk", ascending=False).reset_index(drop=True)
# new["Estimated risk"] = new["risk"] * 100
# new["Priority"] = np.where(new.index < TOP_N, f"Top {TOP_N}", "")
# new["Fees owed"] = new["fees_owed"].map({1: "Yes", 0: "No"})
# new["SU scholarship"] = new["su_scholarship"].map({1: "Yes", 0: "No"})

# # 2025 students, ranked by risk, to test the rule on people whose outcome we know
# past = history[history["cohort"] == 2025].copy()
# past["risk"] = model.predict_proba(past)
# past = past.sort_values("risk", ascending=False)

# st.title("Study Office Decision Support")
# st.caption("A risk score is a prompt to check in, not a judgement about a student.")
# tab_list, tab_rule, tab_why = st.tabs(
#     ["This week's list", "Mistakes of a rule", "Why this student?"])

# # ---------------------------------------------------------------- 1. this week's list
# with tab_list:
#     st.write(f"The {len(new)} new students, from highest to lowest estimated risk. "
#              f"The first {TOP_N} are the suggested outreach list.")
#     st.dataframe(
#         new[["Priority", "student_id", "Estimated risk",
#             "programme", "Fees owed", "SU scholarship"]],
#         hide_index=True, width="stretch", height=600,
#         column_config={
#             "student_id": "Student", "programme": "Programme",
#             "Estimated risk": st.column_config.ProgressColumn("Estimated risk", min_value=0, max_value=100, format="%.0f%%"),
#         },
#     )

# # ---------------------------------------------------------------- 2 + 3. mistakes of a rule, per group
# with tab_rule:
#     st.write("Rule: contact the students with the highest estimated risk. "
#              "We test it on the 2025 students, where we already know who left.")
#     n = st.slider("How many conversations can the office have?",
#                   0, len(past), TOP_N)
#     past["contacted"] = np.arange(len(past)) < n
#     reached, worried, missed, stayed, precision, recall = four_boxes(past)

#     st.markdown(
#         f"### {reached} reached in time, {worried} worried for nothing, {missed} missed")
#     cols = st.columns(4)
#     cols[0].metric("Reached in time", reached,
#                    help="Contacted, and later left.")
#     cols[1].metric("Worried for nothing", worried,
#                    help="Contacted, but stayed.")
#     cols[2].metric("Missed", missed, help="Not contacted, but later left.")
#     cols[3].metric("Stayed, no outreach needed", stayed,
#                    help="Not contacted, and stayed.")
#     st.write(
#         f"**Precision {precision:.0%}**: of the {n} students contacted, {precision:.0%} later left.")
#     st.write(
#         f"**Recall {recall:.0%}**: of the {reached + missed} students who left, {recall:.0%} were contacted.")
#     st.caption(
#         "This looks backwards: it cannot tell us whether a conversation would have changed anyone's mind.")

#     st.markdown("### The same, per group")
#     rows = []
#     for name, group in (("Domestic", past[past["international"] == 0]), ("International", past[past["international"] == 1])):
#         a, b, c, d, p, r = four_boxes(group)
#         rows.append({"Group": name, "Students": len(group), "Reached in time": a, "Worried for nothing": b,
#                      "Missed": c, "Stayed, no outreach needed": d, "Precision": f"{p:.0%}", "Recall": f"{r:.0%}"})
#     st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# # ---------------------------------------------------------------- 4. why is a student on the list?
# with tab_why:
#     st.write("Pick a student to see what moves their estimated risk. These are model signals, not facts about the student.")
#     student = st.selectbox("Student (highest risk first)", new["student_id"])
#     row = new[new["student_id"] == student]
#     effect = model.contributions(row).iloc[0]
#     strongest = effect.reindex(
#         effect.abs().sort_values(ascending=False).index).head(6)

#     st.metric("Estimated risk", f"{row['risk'].iloc[0]:.0%}")
#     raising = [f"{LABEL[f]} ({row[f].iloc[0]})" for f in effect[effect > 0].sort_values(
#         ascending=False).head(3).index]
#     st.write("**Pushing the risk up:** " +
#              (" · ".join(raising) if raising else "nothing stands out"))
#     st.bar_chart(strongest.rename(index=LABEL), horizontal=True)
#     st.caption(
#         "Bars to the right raise the estimated risk, bars to the left lower it.")
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
    # the chosen students live in session_state, so ticks survive switching between the two views
    if "chosen" not in st.session_state:
        st.session_state.chosen = set(new["student_id"].head(TOP_N))

    only_top = st.checkbox(f"Show only the suggested top {TOP_N}", value=True,
                           help="Untick to see all students and change who is selected.")
    st.write(f"The {len(new)} new students, from highest to lowest estimated risk. "
             f"The first {TOP_N} are ticked as the suggested outreach list; tick or untick to change it.")

    view = new.head(TOP_N) if only_top else new
    view = view.assign(
        Priority=view["student_id"].isin(st.session_state.chosen))
    columns = ["Priority", "student_id", "Estimated risk",
               "programme", "Fees owed", "SU scholarship"]
    edited = st.data_editor(
        view[columns], key=f"list_{only_top}", hide_index=True, width="stretch", height=600,
        disabled=[c for c in columns if c != "Priority"],
        column_config={
            "Priority": st.column_config.CheckboxColumn("Priority", width="small"),
            "student_id": "Student", "programme": "Programme",
            "Estimated risk": st.column_config.ProgressColumn("Estimated risk", min_value=0, max_value=100, format="%.0f%%"),
        },
    )
    # remember the ticks of the rows on screen; rows that are hidden keep their old state
    st.session_state.chosen -= set(edited["student_id"])
    st.session_state.chosen |= set(
        edited.loc[edited["Priority"], "student_id"])
    st.caption(
        f"{len(st.session_state.chosen)} students selected for outreach.")

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
