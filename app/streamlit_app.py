"""Streamlit dashboard for NHS England A&E attendances and emergency admissions, 2025/26.

Run with `streamlit run app/streamlit_app.py`. If the database is missing, the app builds it
from the CSV files in data/raw. `python scripts/build_database.py` builds it in advance.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from nhs_ed import queries  # noqa: E402
from nhs_ed.config import DB_PATH, PROCESSED_DIR, RAW_DIR, SOURCE_URL  # noqa: E402
from nhs_ed.metrics import add_rates, pct_within_4h  # noqa: E402
from nhs_ed.pipeline import build  # noqa: E402

st.set_page_config(page_title="NHS A&E Performance 2025/26", layout="wide")

# A colour belongs to an A&E type or a region and does not change with the filters.
TYPE_COLOURS = {"Type 1": "#2a78d6", "Type 2": "#eb6834", "Other": "#1baf7a"}
TYPE_LABELS = {"Type 1": "Type 1", "Type 2": "Type 2", "Other": "Other A&E department"}
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQ_BLUE = "#2a78d6"

# Readable names for chart axes and hover text.
LABELS = {
    "month_start": "Month", "value": "Value", "pct_within_4h": "Within 4 hours, %",
    "emergency_admissions": "Emergency admissions", "admission_ratio_pct": "Admissions per 100 attendances",
    "attendances_used": "Attendances", "region": "Region", "org_name": "Trust", "patients": "Patients",
    "dta_12h_plus": "Over 12 hour waits", "ae_type": "A&E type",
}


# Data access
@st.cache_resource(show_spinner="Building the database from the NHS England source files. This takes a few seconds.")
def ensure_database():
    """Build the SQLite database from the CSV files in data/raw if it does not exist.

    The database is not committed to the repository, so a fresh deployment, for example on
    Streamlit Community Cloud, has to build it. The result is cached, so the build runs once
    per server process and not on every interaction.
    """
    if not DB_PATH.exists():
        result = build(DB_PATH, write_reports=False)
        if result.db_path is None:
            return result.errors
    return []


@st.cache_resource
def get_connection():
    # Opened read-only, so the dashboard cannot modify the data.
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)


if not DB_PATH.exists():
    ensure_database.clear()  # the file was removed after an earlier build, so build it again
failed_checks = ensure_database()
if failed_checks or not DB_PATH.exists():
    st.error("The database could not be built because validation checks failed. "
             "Run `python scripts/build_database.py` locally to see the details.")
    for c in failed_checks:
        st.write(f"{c.name}: {c.detail}")
    st.stop()

con = get_connection()


@st.cache_data
def load_months():
    return queries.months(con)


@st.cache_data
def load_regions():
    return queries.regions(con)


@st.cache_data
def q_monthly_by_type(regs, start, end):
    return queries.monthly_by_type(con, regs, start, end)


@st.cache_data
def q_monthly_by_region(ae_type, start, end):
    return queries.monthly_by_region(con, ae_type, start, end)


@st.cache_data
def q_dta(regs, start, end):
    return queries.dta_waits_monthly(con, regs, start, end)


@st.cache_data
def q_trusts(ae_type, regs, start, end, excl):
    return queries.trust_summary(con, ae_type, regs, start, end, excl)


@st.cache_data
def q_trust_dta(start, end):
    return queries.trust_dta_summary(con, start, end)


@st.cache_data
def q_trust_monthly(ae_type, codes, start, end):
    return queries.trust_monthly(con, ae_type, codes, start, end)


def style(fig, y_title=None, height=420, pct=False):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.12, x=0, title=None),
        xaxis_title=None, yaxis_title=y_title, hovermode="x unified" if fig.data and fig.data[0].type in ("scatter", "bar") else "closest",
    )
    if pct:
        fig.update_yaxes(ticksuffix="%")
    return fig


def fmt_int(x):
    return f"{int(x):,}"


def fmt_pct(x, d=1):
    return "n/a" if pd.isna(x) else f"{x:.{d}f}%"


# Sidebar filters
months = load_months()
labels = months["month_label"].tolist()
all_regions = load_regions()

st.sidebar.title("Filters")
first_label, last_label = st.sidebar.select_slider("Months", options=labels, value=(labels[0], labels[-1]))
start = months.loc[months.month_label == first_label, "month_start"].iloc[0].strftime("%Y-%m-%d")
end = months.loc[months.month_label == last_label, "month_start"].iloc[0].strftime("%Y-%m-%d")
sel_regions = tuple(st.sidebar.multiselect("NHS England regions", all_regions, default=all_regions) or all_regions)
include_booked = st.sidebar.checkbox(
    "Include booked appointment attendances", value=True,
    help="NHS England's published headline figures include booked appointment attendances, which the files report in separate "
         "columns. Ticked, the default, uses the same basis as the published figures. Unticked gives an unbooked view.")
st.sidebar.caption("Rates are always computed from summed counts, never by averaging percentages.")
st.sidebar.markdown(f"[Official source page]({SOURCE_URL})")

st.title("NHS Emergency Department Performance, 2025/26")
st.caption(f"NHS England monthly A&E attendances and emergency admissions, {first_label} to {last_label}, "
           f"{len(sel_regions)} of {len(all_regions)} regions")

monthly = q_monthly_by_type(sel_regions, start, end)
if monthly.empty:
    st.warning("No data for this selection.")
    st.stop()
monthly = add_rates(monthly, include_booked)


def period_by_type(df):
    """Collapse the months into one row per A&E type for the selected period."""
    g = df.groupby("ae_type", as_index=False)[["attendances", "over_4hrs", "booked_attendances", "booked_over_4hrs", "emergency_admissions"]].sum()
    return add_rates(g, include_booked)


tab_over, tab_att, tab_perf, tab_adm, tab_trust, tab_method = st.tabs(
    ["Overview", "Attendance trends", "Four-hour performance", "Emergency admissions", "Trust comparison", "Method and data quality"])

# Overview
with tab_over:
    st.info("A&E types are not blended into one percentage here. Type 1, which covers major emergency departments, Type 2 and "
            "Other A&E department are different kinds of service. Each is reported separately, and the headline figures use Type 1.")
    per_type = period_by_type(monthly).set_index("ae_type")
    t1 = per_type.loc["Type 1"]
    latest = monthly[(monthly.ae_type == "Type 1") & (monthly.month_start == monthly.month_start.max())].iloc[0]
    dta = q_dta(sel_regions, start, end)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Type 1 attendances", fmt_int(t1.attendances_used))
    c2.metric("Type 1 seen within 4 hours", fmt_pct(t1.pct_within_4h), help="Share of Type 1 attendances admitted, transferred or discharged within 4 hours, over the selected months.")
    c3.metric(f"Type 1 in {latest.month_label}", fmt_pct(latest.pct_within_4h))
    c4.metric("Over 12 hour waits, decision to admit", fmt_int(dta.dta_12h_plus.sum()), help="Patients whose wait from decision to admit, or from the end of A&E treatment if later, to admission was 12:00:01 or longer, as in NHS England definition A4. Not split by A&E type. This is the sum over the selected months and regions.")

    st.subheader("By A&E type, shown separately")
    table = per_type.reindex(["Type 1", "Type 2", "Other"]).reset_index()
    table["A&E type"] = table["ae_type"].map(TYPE_LABELS)
    table = table.rename(columns={"attendances_used": "Attendances", "pct_within_4h": "% within 4h", "emergency_admissions": "Emergency admissions via A&E"})
    st.dataframe(table[["A&E type", "Attendances", "% within 4h", "Emergency admissions via A&E"]], hide_index=True, width="stretch",
                 column_config={"Attendances": st.column_config.NumberColumn(format="localized"), "% within 4h": st.column_config.NumberColumn(format="%.1f%%"),
                                "Emergency admissions via A&E": st.column_config.NumberColumn(format="localized")})

    with st.expander("Why are trusts not compared on one overall A&E figure?"):
        pooled = pct_within_4h(per_type.attendances_used.sum(), per_type.over_4hrs_used.sum())
        st.write(f"NHS England also publishes a pooled all A&E departments percentage. Pooling the three types for this selection "
                 f"gives {fmt_pct(pooled)}, against {fmt_pct(t1.pct_within_4h)} for Type 1 alone. The gap comes from service mix and not "
                 f"from how well major departments perform. Type 1 is {t1.attendances_used / per_type.attendances_used.sum() * 100:.0f}% of "
                 "attendances in this selection, and areas with more Other A&E department attendances look better when pooled. Pooled figures are "
                 "reasonable as a national headline but are not a like-for-like basis for comparing areas, so the rankings here use Type 1 only.")

# Attendance trends
with tab_att:
    mode = st.radio("Show", ["Attendances per day", "Total attendances per month"], horizontal=True,
                    help="February has 28 days and the other months have 30 or 31, so per-day figures are fairer for comparing months.")
    v = monthly.assign(value=lambda d: d.attendances_per_day if mode.startswith("Attendances per day") else d.attendances_used)
    v["A&E type"] = v.ae_type.map(TYPE_LABELS)
    fig = px.bar(v, labels=LABELS, x="month_start", y="value", color="A&E type", barmode="stack",
                 color_discrete_map={TYPE_LABELS[k]: c for k, c in TYPE_COLOURS.items()}, category_orders={"A&E type": list(TYPE_LABELS.values())},
                 hover_data={"month_start": "|%b %Y"})
    fig.update_xaxes(tickformat="%b '%y", dtick="M1")
    st.plotly_chart(style(fig, "Attendances per day" if mode.startswith("Attendances per day") else "Attendances"), width="stretch")
    st.caption("Stacked bars show volume only, because counts can be added. Percentages are never stacked or combined.")

    st.subheader("Each type on its own scale")
    fig = px.line(v, labels=LABELS, x="month_start", y="value", color="A&E type", facet_col="A&E type", markers=True,
                  color_discrete_map={TYPE_LABELS[k]: c for k, c in TYPE_COLOURS.items()})
    fig.update_yaxes(matches=None, showticklabels=True)
    fig.update_xaxes(tickformat="%b", dtick="M2", title=None)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_traces(marker=dict(size=8), line=dict(width=2.5))
    fig.update_layout(height=320, showlegend=False, margin=dict(l=10, r=10, t=40, b=10), yaxis_title=None)
    st.plotly_chart(fig, width="stretch")

# Four-hour performance
with tab_perf:
    st.markdown("Percentage of attendances admitted, transferred or discharged within 4 hours. There is one line per A&E type, and the types are not blended.")
    show_types = st.multiselect("A&E types", list(TYPE_LABELS), default=["Type 1", "Type 2", "Other"], format_func=TYPE_LABELS.get)
    v = monthly[monthly.ae_type.isin(show_types)].copy()
    v["A&E type"] = v.ae_type.map(TYPE_LABELS)
    if v.empty:
        st.info("Choose at least one A&E type.")
    else:
        fig = px.line(v, labels=LABELS, x="month_start", y="pct_within_4h", color="A&E type", markers=True,
                      color_discrete_map={TYPE_LABELS[k]: c for k, c in TYPE_COLOURS.items()})
        fig.update_traces(marker=dict(size=8), line=dict(width=2.5), hovertemplate="%{y:.1f}%")
        fig.update_xaxes(tickformat="%b '%y", dtick="M1")
        st.plotly_chart(style(fig, "% within 4 hours", pct=True), width="stretch")

    st.subheader("Type 1 by region")
    reg = add_rates(q_monthly_by_region("Type 1", start, end), include_booked)
    reg = reg[reg.region.isin(sel_regions)]
    fig = px.line(reg, labels=LABELS, x="month_start", y="pct_within_4h", color="region", markers=True,
                  color_discrete_map={r: CATEGORICAL[i] for i, r in enumerate(all_regions)})
    fig.update_traces(marker=dict(size=8), line=dict(width=2.5), hovertemplate="%{y:.1f}%")
    fig.update_xaxes(tickformat="%b '%y", dtick="M1")
    st.plotly_chart(style(fig, "Type 1 within 4 hours, %", pct=True, height=440), width="stretch")
    period_reg = add_rates(reg.groupby("region", as_index=False)[["attendances", "over_4hrs", "booked_attendances", "booked_over_4hrs", "emergency_admissions"]].sum(), include_booked)
    st.dataframe(period_reg.sort_values("pct_within_4h", ascending=False)[["region", "attendances_used", "pct_within_4h"]]
                 .rename(columns={"region": "Region", "attendances_used": "Type 1 attendances", "pct_within_4h": "% within 4h"}),
                 hide_index=True, width="stretch",
                 column_config={"Type 1 attendances": st.column_config.NumberColumn(format="localized"), "% within 4h": st.column_config.NumberColumn(format="%.1f%%")})

# Emergency admissions
with tab_adm:
    v = monthly.copy()
    v["A&E type"] = v.ae_type.map(TYPE_LABELS)
    st.subheader("Emergency admissions via A&E")
    fig = px.bar(v, labels=LABELS, x="month_start", y="emergency_admissions", color="A&E type", barmode="stack",
                 color_discrete_map={TYPE_LABELS[k]: c for k, c in TYPE_COLOURS.items()}, category_orders={"A&E type": list(TYPE_LABELS.values())})
    fig.update_xaxes(tickformat="%b '%y", dtick="M1")
    st.plotly_chart(style(fig, "Admissions"), width="stretch")
    st.caption("Other A&E department and Type 2 admissions are small by comparison. Almost all emergency admissions via A&E come through Type 1.")

    st.subheader("Type 1 admissions per 100 attendances")
    t1m = monthly[monthly.ae_type == "Type 1"]
    fig = px.line(t1m, labels=LABELS, x="month_start", y="admission_ratio_pct", markers=True, color_discrete_sequence=[TYPE_COLOURS["Type 1"]])
    fig.update_traces(marker=dict(size=8), line=dict(width=2.5), hovertemplate="%{y:.1f} per 100")
    fig.update_xaxes(tickformat="%b '%y", dtick="M1")
    st.plotly_chart(style(fig, "Admissions per 100 Type 1 attendances"), width="stretch")
    st.caption("This is a ratio and not a clinical conversion rate. Admissions are those via Type 1 A&E, admission method 21, to the same provider. Attendances exclude patients streamed to same-day emergency care on arrival. The ratio depends on case mix and on local pathways and recording, as the Trust comparison tab shows.")

    st.subheader("Waits from decision to admit to admission")
    dta = q_dta(sel_regions, start, end).melt(id_vars="month_start", value_vars=["dta_4_to_12h", "dta_12h_plus"], var_name="band", value_name="patients")
    dta["Wait band"] = dta.band.map({"dta_4_to_12h": "4 to 12 hours, up to 12:00:00", "dta_12h_plus": "Over 12 hours"})
    fig = px.bar(dta, labels=LABELS, x="month_start", y="patients", color="Wait band", barmode="group",
                 color_discrete_map={"4 to 12 hours, up to 12:00:00": CATEGORICAL[3], "Over 12 hours": CATEGORICAL[7]})
    fig.update_xaxes(tickformat="%b '%y", dtick="M1")
    st.plotly_chart(style(fig, "Patients"), width="stretch")
    st.caption("Under NHS England definitions A3 and A4, the wait runs from the decision to admit, or the end of A&E treatment if later, to admission. A wait of 4 to 12 hours is 04:00:01 to 12:00:00 inclusive, and over 12 hours is 12:00:01 or longer. "
               "The counts are not split by A&E type. For a patient transferred to another provider the wait ends when they are collected, so the counts are not limited to patients admitted by the reporting trust. "
               "This is not the same as total time in A&E.")

# Trust comparison
with tab_trust:
    st.warning("Trusts are compared on Type 1 only, which covers major emergency departments, because that is the type general "
               "acute trusts have in common. Type 2 and Other A&E departments are excluded, and trusts with no Type 1 activity cannot appear. "
               "Differences can still reflect case mix, size and local recording practice, so the comparison is a prompt for questions and not a verdict. "
               "NHS England's definitions say that a patient streamed from a Type 1 department to a co-located Type 3 service is counted as one Type 3 attendance, and that a patient streamed to same-day emergency care on arrival is not counted as an A&E attendance at all. "
               "Trusts with different streaming arrangements therefore have different Type 1 populations.")
    f1, f2, f3 = st.columns([2, 1, 1])
    metric = f1.selectbox("Metric", ["Seen within 4 hours, %", "Type 1 attendances", "Admissions per 100 Type 1 attendances", "Over 12 hour decision-to-admit waits, count"])
    min_att = f2.number_input("Minimum Type 1 attendances in period", 0, 500000, 20000, step=5000,
                              help="Hides small departments so that a few cases cannot swing a percentage.")
    excl = f3.checkbox("Exclude children's and women's trusts", value=True, help="These trusts have a different case mix. They are identified by CHILDREN or WOMEN in the trust name.")

    trusts = add_rates(q_trusts("Type 1", sel_regions, start, end, excl), include_booked)
    trusts = trusts.merge(q_trust_dta(start, end), on="org_code", how="left")
    trusts = trusts[trusts.attendances_used >= min_att]
    metric_col = {"Seen within 4 hours, %": "pct_within_4h", "Type 1 attendances": "attendances_used",
                  "Admissions per 100 Type 1 attendances": "admission_ratio_pct", "Over 12 hour decision-to-admit waits, count": "dta_12h_plus"}[metric]
    if trusts.empty:
        st.info("No trusts match these filters.")
    else:
        view = st.radio("Show", ["Highest 15", "Lowest 15"], horizontal=True)
        ranked = trusts.sort_values(metric_col, ascending=(view == "Lowest 15")).head(15).iloc[::-1]
        fig = px.bar(ranked, labels=LABELS, x=metric_col, y="org_name", orientation="h", color_discrete_sequence=[SEQ_BLUE],
                     hover_data={"region": True, "attendances_used": ":,", "org_name": False})
        fig.update_yaxes(title=None)
        st.plotly_chart(style(fig, None, height=520).update_layout(xaxis_title=metric, hovermode="closest"), width="stretch")
        if metric_col == "dta_12h_plus":
            st.caption("Counts are not adjusted for size, so larger trusts will naturally have more. The source does not split them by A&E type.")
        if metric_col == "admission_ratio_pct":
            st.caption("Ratios range very widely between trusts, as SQL query 10 shows, which suggests differences in how admissions are recorded. They should not be read as a measure of quality.")

        st.subheader("Volume and performance")
        fig = px.scatter(trusts, labels=LABELS, x="attendances_used", y="pct_within_4h", color="region", hover_name="org_name",
                         color_discrete_map={r: CATEGORICAL[i] for i, r in enumerate(all_regions)})
        fig.update_traces(marker=dict(size=10, line=dict(width=2, color="rgba(255,255,255,0.9)")))
        fig.update_xaxes(title="Type 1 attendances in period")
        st.plotly_chart(style(fig, "Type 1 within 4 hours, %", pct=True, height=460).update_layout(hovermode="closest"), width="stretch")

        st.subheader("Trend for chosen trusts")
        options = trusts.sort_values("attendances", ascending=False).set_index("org_code")["org_name"].to_dict()
        chosen = st.multiselect("Trusts, up to 6", list(options), default=list(options)[:3], format_func=options.get, max_selections=6)
        if chosen:
            tm = add_rates(q_trust_monthly("Type 1", tuple(chosen), start, end), include_booked)
            colour_of = {c: CATEGORICAL[i] for i, c in enumerate(chosen)}
            fig = px.line(tm, labels=LABELS, x="month_start", y="pct_within_4h", color="org_name", markers=True,
                          color_discrete_map={options[c]: colour_of[c] for c in chosen})
            nat = add_rates(monthly[monthly.ae_type == "Type 1"][["month_start", "attendances", "over_4hrs", "booked_attendances", "booked_over_4hrs", "emergency_admissions"]], include_booked)
            fig.add_trace(go.Scatter(x=nat.month_start, y=nat.pct_within_4h, name="Type 1, selected regions", mode="lines",
                                     line=dict(color="#888888", width=2, dash="dash"), hovertemplate="%{y:.1f}%"))
            fig.update_traces(selector=dict(mode="lines+markers"), marker=dict(size=8), line=dict(width=2.5), hovertemplate="%{y:.1f}%")
            fig.update_xaxes(tickformat="%b '%y", dtick="M1")
            st.plotly_chart(style(fig, "Type 1 within 4 hours, %", pct=True), width="stretch")

        st.subheader("Table")
        out = trusts.sort_values("pct_within_4h", ascending=False)[["org_code", "org_name", "region", "attendances_used", "pct_within_4h", "emergency_admissions", "admission_ratio_pct", "dta_12h_plus"]]
        out.columns = ["Org code", "Trust", "Region", "Type 1 attendances", "% within 4h", "Type 1 emergency admissions", "Admissions per 100 attendances", "Over 12 hour waits"]
        st.dataframe(out, hide_index=True, width="stretch", column_config={
            "Type 1 attendances": st.column_config.NumberColumn(format="localized"), "% within 4h": st.column_config.NumberColumn(format="%.1f"),
            "Type 1 emergency admissions": st.column_config.NumberColumn(format="localized"), "Admissions per 100 attendances": st.column_config.NumberColumn(format="%.1f"),
            "Over 12 hour waits": st.column_config.NumberColumn(format="localized")})
        st.download_button("Download table as CSV", out.to_csv(index=False).encode(), "type1_trust_comparison.csv", "text/csv")

# Method and data quality
with tab_method:
    st.subheader("Definitions used in this dashboard")
    st.markdown(
        "- Within 4 hours, as a percentage, is attendances minus attendances over 4 hours, divided by attendances and multiplied by 100. It is calculated for one A&E type from summed counts.\n"
        "- Booked appointments are separate columns in the source. NHS England's headline figures include them, so the default adds them to attendances and to over-4-hour counts. The sidebar option gives an unbooked view.\n"
        "- Type 1 is a consultant-led 24-hour emergency department with full resuscitation facilities. Type 2 is a consultant-led single specialty service, such as ophthalmology or dental. Other A&E department is Type 3, which covers urgent treatment centres. Minor injury units, urgent care centres and walk-in centres that are not urgent treatment centres continue to report as Type 3. These follow NHS England definitions version 5.0.\n"
        "- These are the source's own column groups. Each is reported separately, and the only pooled figure is the labelled comparison on the Overview tab.\n"
        "- Admissions per 100 attendances is Type 1 emergency admissions via A&E divided by Type 1 attendances, including booked, and multiplied by 100. It is a ratio and not a conversion rate.\n"
        "- Decision-to-admit waits are patients who waited 04:00:01 to 12:00:00, which is 4 to 12 hours, or 12:00:01 or longer, which is over 12 hours, from the decision to admit, or the end of A&E treatment if later, to admission. They are not split by A&E type.\n"
        "- Other emergency admissions are not used in the analysis. They are emergency admissions that did not come through any A&E department of the same provider, such as direct admission by a GP, the bed bureau or an outpatient clinic, or transfers in from another hospital. This is definition B1iv.\n"
        "- Attendances per day divides by the days in the month, which is 28 to 31, so that February is comparable.")
    st.subheader("Validation results")
    report = PROCESSED_DIR / "validation_report.csv"
    if report.exists():
        st.dataframe(pd.read_csv(report), hide_index=True, width="stretch")
    else:
        st.info("Run `python scripts/build_database.py` to generate the validation report.")
    manifest = RAW_DIR.parent / "MANIFEST.csv"
    if manifest.exists():
        st.subheader("Source files analysed")
        st.dataframe(pd.read_csv(manifest).drop(columns=["source_page"]), hide_index=True, width="stretch")
    st.subheader("Source and citation")
    st.markdown(f"NHS England, *A&E Attendances and Emergency Admissions 2025-26*, monthly provider-level CSV files: <{SOURCE_URL}>. "
                "Contains public sector information licensed under the Open Government Licence v3.0. "
                "This is an independent project. It is not produced or endorsed by NHS England.")
