import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Investment Calculator", page_icon="📈", layout="wide")

st.markdown("<style>[data-testid='stDeployButton'] { display: none; }</style>", unsafe_allow_html=True)

st.title("Investment Calculator")
st.markdown("Plan and visualize your investment growth over time.")

CALC_TABS = [
    ("compound", "Compound Interest"),
    ("sip", "SIP / Regular Contributions"),
    ("goal", "Goal Planner"),
    ("mortgage", "Mortgage Calculator"),
]
_slug_to_label = dict(CALC_TABS)
_labels = [label for _, label in CALC_TABS]
_label_to_slug = {label: slug for slug, label in CALC_TABS}

_requested_slug = st.query_params.get("calc", "compound")
if _requested_slug not in _slug_to_label:
    _requested_slug = "compound"

selected_label = st.radio(
    "Calculator",
    _labels,
    index=_labels.index(_slug_to_label[_requested_slug]),
    horizontal=True,
    label_visibility="collapsed",
    key="calc_nav",
)
selected_slug = _label_to_slug[selected_label]
if st.query_params.get("calc") != selected_slug:
    st.query_params["calc"] = selected_slug

# --- Tab 1: Compound Interest ---
if selected_slug == "compound":
    st.header("Compound Interest Calculator")

    col1, col2 = st.columns([1, 2])

    with col1:
        principal = st.number_input("Initial Investment ($)", min_value=0, value=10000, step=500, format="%d")
        annual_rate = st.slider("Annual Return Rate (%)", min_value=0.0, max_value=30.0, value=7.0, step=0.1)
        years = st.slider("Investment Period (Years)", min_value=1, max_value=50, value=20)

    year_range = np.arange(0, years + 1)
    balances = [principal * (1 + annual_rate / 100) ** y for y in year_range]
    final_value = balances[-1]
    total_gain = final_value - principal

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=year_range, y=balances, mode="lines", name="Balance", fill="tozeroy", line=dict(color="#2ecc71", width=2)))
        fig.add_trace(go.Scatter(x=year_range, y=[principal] * len(year_range), mode="lines", name="Principal", line=dict(color="#95a5a6", dash="dash")))
        fig.update_layout(title="Portfolio Growth", xaxis_title="Years", yaxis_title="Value ($)", yaxis_tickformat="$,.0f", hovermode="x unified")
        st.plotly_chart(fig, width='stretch')

    m1, m2, m3 = st.columns(3)
    m1.metric("Final Value", f"${final_value:,.2f}")
    m2.metric("Total Gain", f"${total_gain:,.2f}")
    m3.metric("Return", f"{(total_gain / principal * 100):.1f}%")


# --- Tab 2: SIP / Regular Contributions ---
if selected_slug == "sip":
    st.header("SIP / Regular Contribution Calculator")

    col1, col2 = st.columns([1, 2])

    with col1:
        sip_principal = st.number_input("Initial Investment ($)", min_value=0, value=5000, step=500, key="sip_principal", format="%d")
        monthly_contrib = st.number_input("Monthly Contribution ($)", min_value=0, value=500, step=50, format="%d")
        sip_rate = st.slider("Annual Return Rate (%)", min_value=0.0, max_value=30.0, value=8.0, step=0.1, key="sip_rate")
        sip_years = st.slider("Investment Period (Years)", min_value=1, max_value=50, value=25, key="sip_years")

    monthly_rate = sip_rate / 100 / 12
    months = sip_years * 12
    balances_sip = []
    contributions = []
    balance = sip_principal
    total_contributed = sip_principal

    for m in range(months + 1):
        if m > 0:
            balance = balance * (1 + monthly_rate) + monthly_contrib
            total_contributed += monthly_contrib
        balances_sip.append(balance)
        contributions.append(total_contributed)

    year_labels = [m / 12 for m in range(months + 1)]
    final_sip = balances_sip[-1]
    total_cont = contributions[-1]
    sip_gain = final_sip - total_cont

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=year_labels, y=balances_sip, name="Portfolio Value", fill="tozeroy", line=dict(color="#3498db", width=2)))
        fig2.add_trace(go.Scatter(x=year_labels, y=contributions, name="Total Contributed", line=dict(color="#e74c3c", dash="dash")))
        fig2.update_layout(title="Portfolio Growth with Contributions", xaxis_title="Years", yaxis_title="Value ($)", yaxis_tickformat="$,.0f", hovermode="x unified")
        st.plotly_chart(fig2, width='stretch')

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Value", f"${final_sip:,.2f}")
    m2.metric("Total Contributed", f"${total_cont:,.2f}")
    m3.metric("Investment Gain", f"${sip_gain:,.2f}")
    m4.metric("Return on Contributions", f"{(sip_gain / total_cont * 100):.1f}%")


# --- Tab 3: Goal Planner ---
if selected_slug == "goal":
    st.header("Goal Planner")
    st.markdown("Find out how much to invest monthly to reach a target.")

    col1, col2 = st.columns([1, 2])

    with col1:
        goal_amount = st.number_input("Target Amount ($)", min_value=1000, value=500000, step=10000, format="%d")
        goal_initial = st.number_input("Initial Investment ($)", min_value=0, value=10000, step=1000, format="%d")
        goal_rate = st.slider("Expected Annual Return (%)", min_value=0.1, max_value=30.0, value=7.0, step=0.1, key="goal_rate")
        goal_years = st.slider("Time to Goal (Years)", min_value=1, max_value=50, value=20, key="goal_years")

    mr = goal_rate / 100 / 12
    n = goal_years * 12
    future_principal = goal_initial * (1 + mr) ** n
    remaining = goal_amount - future_principal

    if mr > 0 and remaining > 0:
        required_monthly = remaining * mr / ((1 + mr) ** n - 1)
    elif remaining <= 0:
        required_monthly = 0.0
    else:
        required_monthly = remaining / n

    with col2:
        rates = np.linspace(1, 20, 100)
        monthly_needed = []
        for rate in rates:
            _mr = rate / 100 / 12
            _fp = goal_initial * (1 + _mr) ** n
            _rem = goal_amount - _fp
            if _mr > 0 and _rem > 0:
                monthly_needed.append(_rem * _mr / ((1 + _mr) ** n - 1))
            elif _rem <= 0:
                monthly_needed.append(0)
            else:
                monthly_needed.append(_rem / n)

        fig3 = px.line(x=rates, y=monthly_needed, labels={"x": "Annual Return Rate (%)", "y": "Required Monthly ($)"}, title="Monthly Contribution vs. Return Rate")
        fig3.add_vline(x=goal_rate, line_dash="dash", line_color="red", annotation_text=f"Your rate: {goal_rate}%")
        fig3.update_traces(line=dict(color="#9b59b6", width=2))
        fig3.update_layout(yaxis_tickformat="$,.0f")
        st.plotly_chart(fig3, width='stretch')

    m1, m2, m3 = st.columns(3)
    m1.metric("Required Monthly Contribution", f"${max(required_monthly, 0):,.2f}")
    m2.metric("Growth from Initial Investment", f"${future_principal:,.2f}")
    m3.metric("Needed from Contributions", f"${max(remaining, 0):,.2f}")


# --- Tab 4: Mortgage Calculator ---
if selected_slug == "mortgage":
    st.header("Mortgage Calculator")
    st.markdown("See how much interest you pay over the life of your loan — and how much you can save by paying extra principal each month.")

    _qp = st.query_params
    _today = pd.Timestamp.today()

    def _qp_int(k, d, lo=None, hi=None):
        try:
            v = int(_qp.get(k, d))
        except (TypeError, ValueError):
            return d
        if lo is not None: v = max(lo, v)
        if hi is not None: v = min(hi, v)
        return v

    def _qp_float(k, d, lo=None, hi=None):
        try:
            v = float(_qp.get(k, d))
        except (TypeError, ValueError):
            return d
        if lo is not None: v = max(lo, v)
        if hi is not None: v = min(hi, v)
        return v

    def _qp_bool(k, d):
        raw = _qp.get(k)
        if raw is None: return d
        return str(raw).lower() in ("1", "true", "yes", "on")

    _term_options = [10, 15, 20, 25, 30]
    _d_term = _qp_int("term", 30)
    if _d_term not in _term_options: _d_term = 30
    _d_om = _qp_int("origMonth", _today.month, lo=1, hi=12)
    _d_oy = _qp_int("origYear", _today.year, lo=1980, hi=2100)
    _qp_defaults = {
        "mort_home_price":        _qp_int("price", 400000, lo=10000),
        "mort_down_pct":          _qp_int("down", 20, lo=0, hi=50),
        "mort_rate":              _qp_float("rate", 6.750, lo=0.0, hi=20.0),
        "mort_term":              _d_term,
        "mort_orig_month":        _d_om,
        "mort_orig_year":         _d_oy,
        "mort_biweekly":          _qp_bool("biweekly", False),
        "mort_extra":             _qp_int("extra", 0, lo=0),
        "mort_extra_start_month": _qp_int("extraMonth", _d_om, lo=1, hi=12),
        "mort_extra_start_year":  _qp_int("extraYear", _d_oy, lo=1980, hi=2100),
    }
    for _k, _v in _qp_defaults.items():
        st.session_state.setdefault(_k, _v)

    col1, col2 = st.columns([1, 2])

    with col1:
        home_price = st.number_input("Home Price ($)", min_value=10000, step=5000, format="%d", key="mort_home_price")
        down_pct = st.slider("Down Payment (%)", min_value=0, max_value=50, step=1, key="mort_down_pct")
        mort_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=20.0,
                                    step=0.05, format="%.3f",
                                    help="Type any value (e.g. 3.575). Arrows step in 0.05% increments.",
                                    key="mort_rate")
        mort_years = st.selectbox("Loan Term (Years)", options=_term_options, key="mort_term")
        oc1, oc2 = st.columns(2)
        with oc1:
            orig_month = st.selectbox(
                "Origination Month",
                options=list(range(1, 13)),
                format_func=lambda m: pd.Timestamp(2000, m, 1).strftime("%B"),
                key="mort_orig_month",
            )
        with oc2:
            orig_year = st.number_input("Origination Year", min_value=1980, max_value=2100,
                                        step=1, key="mort_orig_year")
        biweekly = st.checkbox(
            "Bi-weekly payments (13th payment/yr)",
            help="Modeled as one extra full monthly payment per year, applied as additional principal spread evenly across the 12 months (monthly_payment / 12).",
            key="mort_biweekly",
        )
        extra_payment = st.number_input("Extra Monthly Principal ($)", min_value=0, step=50, format="%d",
                                        help="Additional amount paid toward principal each month on the accelerated schedule",
                                        key="mort_extra")
        ec1, ec2 = st.columns(2)
        with ec1:
            extra_start_month = st.selectbox(
                "Extra Payments Start Month",
                options=list(range(1, 13)),
                format_func=lambda m: pd.Timestamp(2000, m, 1).strftime("%B"),
                key="mort_extra_start_month",
                help="When the extra monthly principal payments begin. Defaults to loan origination.",
            )
        with ec2:
            extra_start_year = st.number_input(
                "Extra Payments Start Year",
                min_value=1980, max_value=2100,
                step=1, key="mort_extra_start_year",
            )

    st.query_params.update({
        "calc": "mortgage",
        "price": str(int(home_price)),
        "down": str(int(down_pct)),
        "rate": f"{mort_rate:.3f}",
        "term": str(int(mort_years)),
        "origMonth": str(int(orig_month)),
        "origYear": str(int(orig_year)),
        "biweekly": "1" if biweekly else "0",
        "extra": str(int(extra_payment)),
        "extraMonth": str(int(extra_start_month)),
        "extraYear": str(int(extra_start_year)),
    })
    st.caption("Your inputs are saved in this page's URL — copy it from your browser's address bar to share or bookmark.")

    down_amount = home_price * down_pct / 100
    loan_amount = home_price - down_amount
    monthly_rate = mort_rate / 100 / 12
    n_payments = mort_years * 12

    if monthly_rate > 0:
        monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** n_payments / ((1 + monthly_rate) ** n_payments - 1)
    else:
        monthly_payment = loan_amount / n_payments

    orig_date = pd.Timestamp(year=int(orig_year), month=int(orig_month), day=1)
    extra_start_date = pd.Timestamp(year=int(extra_start_year), month=int(extra_start_month), day=1)
    extra_start_idx = max(
        1,
        (extra_start_date.year - orig_date.year) * 12 + (extra_start_date.month - orig_date.month) + 1,
    )
    biweekly_extra = monthly_payment / 12 if biweekly else 0.0

    def build_schedule(loan, monthly_rate, base_payment, orig_date,
                       extra=0.0, extra_start=1, recurring_extra=0.0):
        """Month-by-month amortization. Row 0 is origination (no payment); each later row is after one payment.
        `extra` kicks in at month index `extra_start` (1-indexed); `recurring_extra` applies every month."""
        rows = [{
            "Date": orig_date, "Month": 0,
            "Payment": 0.0, "Extra Principal": 0.0,
            "Principal": 0.0, "Interest": 0.0,
            "Cumulative Interest": 0.0, "Balance": float(loan),
        }]
        balance = float(loan)
        cum_interest = 0.0
        month_idx = 0
        while balance > 1e-6:
            month_idx += 1
            interest_charge = balance * monthly_rate
            intended_extra = recurring_extra + (extra if month_idx >= extra_start else 0.0)
            regular_principal = min(max(base_payment - interest_charge, 0.0), balance)
            if regular_principal <= 0 and intended_extra <= 0:
                break  # payment doesn't even cover interest — avoid infinite loop
            applied_extra = min(intended_extra, balance - regular_principal)
            principal_applied = regular_principal + applied_extra
            cum_interest += interest_charge
            balance -= principal_applied
            rows.append({
                "Date": orig_date + pd.DateOffset(months=month_idx),
                "Month": month_idx,
                "Payment": interest_charge + principal_applied,
                "Extra Principal": applied_extra,
                "Principal": principal_applied,
                "Interest": interest_charge,
                "Cumulative Interest": cum_interest,
                "Balance": max(balance, 0.0),
            })
        return pd.DataFrame(rows)

    std_df = build_schedule(loan_amount, monthly_rate, monthly_payment, orig_date)
    acc_df = build_schedule(
        loan_amount, monthly_rate, monthly_payment, orig_date,
        extra=extra_payment, extra_start=extra_start_idx, recurring_extra=biweekly_extra,
    )

    has_acceleration = extra_payment > 0 or biweekly
    acc_label_parts = []
    if biweekly:
        acc_label_parts.append("bi-weekly")
    if extra_payment > 0:
        acc_label_parts.append(f"+${extra_payment:,}/mo")
    acc_label = "Accelerated (" + ", ".join(acc_label_parts) + ")" if acc_label_parts else "Accelerated"

    std_balances = std_df["Balance"].tolist()
    std_interests = std_df["Cumulative Interest"].tolist()
    std_dates_x = std_df["Date"].tolist()
    acc_balances = acc_df["Balance"].tolist()
    acc_interests = acc_df["Cumulative Interest"].tolist()
    acc_dates_x = acc_df["Date"].tolist()

    std_months = len(std_df) - 1
    acc_months = len(acc_df) - 1
    std_total_interest = std_interests[-1]
    acc_total_interest = acc_interests[-1]
    interest_saved = std_total_interest - acc_total_interest
    months_saved = std_months - acc_months

    with col2:
        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(
            x=std_dates_x, y=std_balances,
            name="Standard schedule",
            line=dict(color="#e74c3c", width=2),
            fill="tozeroy", fillcolor="rgba(231,76,60,0.08)"
        ))
        if has_acceleration:
            fig_m.add_trace(go.Scatter(
                x=acc_dates_x, y=acc_balances,
                name=acc_label,
                line=dict(color="#2ecc71", width=2),
                fill="tozeroy", fillcolor="rgba(46,204,113,0.12)"
            ))
            if extra_payment > 0 and extra_start_idx > 1:
                _vx = extra_start_date.to_pydatetime()
                fig_m.add_shape(
                    type="line", xref="x", yref="paper",
                    x0=_vx, x1=_vx, y0=0, y1=1,
                    line=dict(color="#2ecc71", width=1, dash="dot"),
                )
                fig_m.add_annotation(
                    x=_vx, y=1, xref="x", yref="paper",
                    text="extra payments start",
                    showarrow=False, yanchor="bottom",
                    font=dict(color="#2ecc71"),
                )
        fig_m.update_layout(
            title="Remaining Loan Balance Over Time",
            xaxis_title="Year",
            yaxis_title="Balance ($)",
            yaxis_tickformat="$,.0f",
            xaxis=dict(type="date", tickformat="%Y"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_m, width='stretch')

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Loan Amount", f"${loan_amount:,.0f}")
    m2.metric("Monthly Payment", f"${monthly_payment:,.2f}")
    m3.metric("Total Interest (Standard)", f"${std_total_interest:,.0f}")
    if has_acceleration:
        m4.metric("Interest Saved", f"${interest_saved:,.0f}", delta=f"-{months_saved} months")
    else:
        m4.metric("Total Cost", f"${loan_amount + std_total_interest:,.0f}")

    st.divider()

    if has_acceleration:
        st.subheader(f"Payoff Comparison — Standard vs. {acc_label}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Standard Payoff", f"{std_months // 12}y {std_months % 12}m")
        c2.metric("Accelerated Payoff", f"{acc_months // 12}y {acc_months % 12}m")
        c3.metric("Time Saved", f"{months_saved // 12}y {months_saved % 12}m")
        c4.metric("Interest Saved", f"${interest_saved:,.0f}")

        fig_int = go.Figure()
        fig_int.add_trace(go.Scatter(
            x=std_dates_x, y=std_interests,
            name="Standard schedule",
            line=dict(color="#e74c3c", width=2)
        ))
        fig_int.add_trace(go.Scatter(
            x=acc_dates_x, y=acc_interests,
            name=acc_label,
            line=dict(color="#2ecc71", width=2)
        ))
        fig_int.update_layout(
            title="Cumulative Interest Paid Over Time",
            xaxis_title="Year",
            yaxis_title="Cumulative Interest ($)",
            yaxis_tickformat="$,.0f",
            xaxis=dict(type="date", tickformat="%Y"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_int, width='stretch')

    def _render_schedule(df, include_extra_column):
        display = df.iloc[1:].drop(columns=["Cumulative Interest"]).copy()
        if not include_extra_column:
            display = display.drop(columns=["Extra Principal"])
        money_cols = ["Payment", "Principal", "Interest", "Balance"] + (
            ["Extra Principal"] if include_extra_column else []
        )
        col_config = {
            "Date": st.column_config.DateColumn("Date", format="MMM YYYY"),
            "Month": st.column_config.NumberColumn("Month", format="%d"),
        }
        for c in money_cols:
            col_config[c] = st.column_config.NumberColumn(c, format="$%.2f")
        st.dataframe(display, width='stretch', hide_index=True, column_config=col_config)

    std_y, std_m = divmod(std_months, 12)
    with st.expander(f"Standard amortization schedule — {std_y}y {std_m}m, {std_months} payments"):
        _render_schedule(std_df, include_extra_column=False)

    if has_acceleration:
        acc_y, acc_m = divmod(acc_months, 12)
        with st.expander(f"Accelerated amortization schedule — {acc_label}, {acc_y}y {acc_m}m, {acc_months} payments"):
            _render_schedule(acc_df, include_extra_column=True)
