import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Calx: Add It Up", page_icon="📈", layout="wide")
st.markdown("<style>[data-testid='stDeployButton'] { display: none; }</style>", unsafe_allow_html=True)

st.title("Calx: Add It Up")
st.markdown("Let's do the numbers.")


def _qp_int(k, d, lo=None, hi=None):
    try:
        v = int(st.query_params.get(k, d))
    except (TypeError, ValueError):
        return d
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v

def _qp_float(k, d, lo=None, hi=None):
    try:
        v = float(st.query_params.get(k, d))
    except (TypeError, ValueError):
        return d
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v

def _qp_bool(k, d):
    raw = st.query_params.get(k)
    if raw is None: return d
    return str(raw).lower() in ("1", "true", "yes", "on")

_today = pd.Timestamp.today()
SHARE_CAPTION = "Your inputs are saved in this page's URL — copy it from your browser's address bar to share or bookmark."


def _money_tag(v):
    """Compact a dollar amount for use in a filename: 477000 -> '477k', 1_250_000 -> '1.2M'."""
    v = abs(float(v))
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if v >= 1_000:
        return f"{round(v / 1_000)}k"
    return f"{int(round(v))}"


def _rate_tag(r):
    """Format a rate without trailing zeros: 8.0 -> '8', 6.75 -> '6.75'."""
    return f"{r:.2f}".rstrip("0").rstrip(".")


def _dur_tag(months):
    """Compact a span of months: 72 -> '6y', 78 -> '6y6m', 0 -> '0m'."""
    y, m = divmod(int(months), 12)
    return (f"{y}y" if y else "") + (f"{m}m" if m else "") or "0m"


def _png_config(filename):
    """st.plotly_chart config that names the modebar PNG download after its contents."""
    return {"toImageButtonOptions": {"filename": filename, "format": "png"}}

tab_savings, tab_debt = st.tabs(["Savings", "Debt"])


# ─── Savings Tab ─────────────────────────────────────────────────────────────
with tab_savings:
    st.header("Savings Calculator")
    st.markdown("Project the growth of an account over time with optional regular contributions.")

    _sav_rate_default = _qp_float("sRate", 8.0, lo=0.0, hi=30.0)
    _sav_defaults = {
        "sav_principal":   _qp_int("sPrincipal", 0, lo=0),
        "sav_monthly":     _qp_int("sMonthly", 500, lo=0),
        "sav_rate_num":    _sav_rate_default,
        "sav_rate_slide":  min(max(_sav_rate_default, 2.0), 20.0),
        "sav_years":       _qp_int("sYears", 25, lo=1, hi=50),
        "sav_start_month": _qp_int("sStartMonth", _today.month, lo=1, hi=12),
        "sav_start_year":  _qp_int("sStartYear", _today.year, lo=1980, hi=2100),
    }
    for _k, _v in _sav_defaults.items():
        st.session_state.setdefault(_k, _v)

    def _sav_slider_to_input():
        st.session_state["sav_rate_num"] = st.session_state["sav_rate_slide"]

    def _sav_input_to_slider():
        v = st.session_state["sav_rate_num"]
        st.session_state["sav_rate_slide"] = min(max(v, 2.0), 20.0)

    col1, col2 = st.columns([1, 2])

    with col1:
        sav_principal = st.number_input(
            "Initial Investment ($)", min_value=0, step=500, format="%d", key="sav_principal"
        )
        sav_monthly = st.number_input(
            "Monthly Contribution ($)", min_value=0, step=50, format="%d", key="sav_monthly"
        )
        sav_rate = st.number_input(
            "Annual Return Rate (%)", min_value=0.0, max_value=30.0, step=0.05, format="%.2f",
            help="Type any rate, or drag the slider below (2–20%).",
            key="sav_rate_num", on_change=_sav_input_to_slider,
        )
        st.slider(
            "Rate slider", min_value=2.0, max_value=20.0, step=0.05, format="%.2f",
            key="sav_rate_slide", on_change=_sav_slider_to_input, label_visibility="collapsed",
        )
        sav_years = st.slider("Investment Period (Years)", min_value=1, max_value=50, key="sav_years")
        sc1, sc2 = st.columns(2)
        with sc1:
            sav_start_month = st.selectbox(
                "Start Month", options=list(range(1, 13)),
                format_func=lambda m: pd.Timestamp(2000, m, 1).strftime("%B"),
                key="sav_start_month",
            )
        with sc2:
            sav_start_year = st.number_input(
                "Start Year", min_value=1980, max_value=2100, step=1, key="sav_start_year"
            )

    start_date = pd.Timestamp(year=int(sav_start_year), month=int(sav_start_month), day=1)
    monthly_rate = sav_rate / 100 / 12
    months = sav_years * 12

    schedule_rows = [{
        "Date": start_date, "Month": 0,
        "Starting Balance": 0.0, "Contribution": float(sav_principal),
        "Interest Earned": 0.0, "Ending Balance": float(sav_principal),
    }]
    balance = float(sav_principal)
    total_contributed = float(sav_principal)
    balances = [balance]
    contributions = [total_contributed]
    month_dates = [start_date]
    for m in range(1, months + 1):
        starting = balance
        interest = balance * monthly_rate
        balance = balance + interest + sav_monthly
        total_contributed += sav_monthly
        balances.append(balance)
        contributions.append(total_contributed)
        month_dates.append(start_date + pd.DateOffset(months=m))
        schedule_rows.append({
            "Date": month_dates[-1], "Month": m,
            "Starting Balance": starting, "Contribution": float(sav_monthly),
            "Interest Earned": interest, "Ending Balance": balance,
        })

    final_val = balances[-1]
    total_cont = contributions[-1]
    sav_gain = final_val - total_cont

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=month_dates, y=balances, name="Portfolio Value",
            fill="tozeroy", line=dict(color="#3498db", width=2),
        ))
        if total_cont > 0:
            fig.add_trace(go.Scatter(
                x=month_dates, y=contributions, name="Total Contributed",
                line=dict(color="#e74c3c", dash="dash"),
            ))
        _sav_y_max = max(max(balances), max(contributions)) if max(balances) > 0 else 1
        fig.update_layout(
            title="Portfolio Growth",
            xaxis_title="Year", yaxis_title="Value ($)",
            yaxis=dict(tickformat="$,.0f", range=[0, _sav_y_max * 1.1]),
            xaxis=dict(type="date", tickformat="%Y"),
            hovermode="x unified",
        )
        _sav_fname = f"savings-{_money_tag(final_val)}-after-{int(sav_years)}y-at-{_rate_tag(sav_rate)}pct"
        st.plotly_chart(fig, width='stretch', config=_png_config(_sav_fname))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Final Value", f"${final_val:,.2f}")
    m2.metric("Total Contributed", f"${total_cont:,.2f}")
    m3.metric("Investment Gain", f"${sav_gain:,.2f}")
    m4.metric("Return on Contributions", f"{(sav_gain / total_cont * 100):.1f}%" if total_cont > 0 else "—")

    with st.expander(f"Month-by-month schedule ({months} months)"):
        st.dataframe(
            pd.DataFrame(schedule_rows),
            width='stretch', hide_index=True,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="MMM YYYY"),
                "Month": st.column_config.NumberColumn("Month", format="%d"),
                "Starting Balance": st.column_config.NumberColumn("Starting Balance", format="$%.2f"),
                "Contribution": st.column_config.NumberColumn("Contribution", format="$%.2f"),
                "Interest Earned": st.column_config.NumberColumn("Interest Earned", format="$%.2f"),
                "Ending Balance": st.column_config.NumberColumn("Ending Balance", format="$%.2f"),
            },
        )

    st.query_params.update({
        "sPrincipal": str(int(sav_principal)),
        "sMonthly":   str(int(sav_monthly)),
        "sRate":      f"{sav_rate:.2f}",
        "sYears":     str(int(sav_years)),
        "sStartMonth": str(int(sav_start_month)),
        "sStartYear":  str(int(sav_start_year)),
    })
    st.caption(SHARE_CAPTION)


# ─── Debt Tab ─────────────────────────────────────────────────────────────────
with tab_debt:
    st.header("Debt Calculator")
    st.markdown("See how much interest you pay over the life of your loan — and how much you can save by paying extra principal each month.")

    _term_options = [10, 15, 20, 25, 30]
    _d_term = _qp_int("dTerm", 30)
    if _d_term not in _term_options: _d_term = 30
    _d_om = _qp_int("dOrigMonth", _today.month, lo=1, hi=12)
    _d_oy = _qp_int("dOrigYear", _today.year, lo=1980, hi=2100)
    _debt_rate_default = _qp_float("dRate", 6.750, lo=0.0, hi=20.0)
    _debt_defaults = {
        "debt_loan":              _qp_int("dLoan", 400000, lo=10000),
        "debt_rate_num":          _debt_rate_default,
        "debt_rate_slide":        min(max(_debt_rate_default, 2.0), 20.0),
        "debt_term":              _d_term,
        "debt_orig_month":        _d_om,
        "debt_orig_year":         _d_oy,
        "debt_biweekly":          _qp_bool("dBiweekly", False),
        "debt_extra":             _qp_int("dExtra", 0, lo=0),
        "debt_extra_start_month": _qp_int("dExtraMonth", _d_om, lo=1, hi=12),
        "debt_extra_start_year":  _qp_int("dExtraYear", _d_oy, lo=1980, hi=2100),
    }
    for _k, _v in _debt_defaults.items():
        st.session_state.setdefault(_k, _v)

    def _debt_slider_to_input():
        st.session_state["debt_rate_num"] = st.session_state["debt_rate_slide"]

    def _debt_input_to_slider():
        v = st.session_state["debt_rate_num"]
        st.session_state["debt_rate_slide"] = min(max(v, 2.0), 20.0)

    col1, col2 = st.columns([1, 2])

    with col1:
        debt_loan = st.number_input(
            "Loan Amount ($)", min_value=10000, step=5000, format="%d", key="debt_loan"
        )
        debt_rate = st.number_input(
            "Annual Interest Rate (%)", min_value=0.0, max_value=20.0, step=0.05, format="%.3f",
            help="Type any rate, or drag the slider below (2–20%).",
            key="debt_rate_num", on_change=_debt_input_to_slider,
        )
        st.slider(
            "Rate slider", min_value=2.0, max_value=20.0, step=0.05, format="%.2f",
            key="debt_rate_slide", on_change=_debt_slider_to_input, label_visibility="collapsed",
        )
        debt_years = st.selectbox("Loan Term (Years)", options=_term_options, key="debt_term")
        oc1, oc2 = st.columns(2)
        with oc1:
            orig_month = st.selectbox(
                "Origination Month", options=list(range(1, 13)),
                format_func=lambda m: pd.Timestamp(2000, m, 1).strftime("%B"),
                key="debt_orig_month",
            )
        with oc2:
            orig_year = st.number_input(
                "Origination Year", min_value=1980, max_value=2100, step=1, key="debt_orig_year"
            )
        biweekly = st.checkbox(
            "Bi-weekly payments (13th payment/yr)",
            help="Modeled as one extra full monthly payment per year, applied as additional principal spread evenly across 12 months (monthly_payment / 12).",
            key="debt_biweekly",
        )
        extra_payment = st.number_input(
            "Extra Monthly Principal ($)", min_value=0, step=50, format="%d",
            help="Additional amount paid toward principal each month on the accelerated schedule.",
            key="debt_extra",
        )
        ec1, ec2 = st.columns(2)
        with ec1:
            extra_start_month = st.selectbox(
                "Extra Payments Start Month", options=list(range(1, 13)),
                format_func=lambda m: pd.Timestamp(2000, m, 1).strftime("%B"),
                key="debt_extra_start_month",
                help="When the extra monthly principal payments begin. Defaults to loan origination.",
            )
        with ec2:
            extra_start_year = st.number_input(
                "Extra Payments Start Year", min_value=1980, max_value=2100,
                step=1, key="debt_extra_start_year",
            )

    loan_amount = float(debt_loan)
    monthly_rate = debt_rate / 100 / 12
    n_payments = debt_years * 12

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

    def build_schedule(loan, m_rate, base_payment, orig_date,
                       extra=0.0, extra_start=1, recurring_extra=0.0):
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
            interest_charge = balance * m_rate
            intended_extra = recurring_extra + (extra if month_idx >= extra_start else 0.0)
            regular_principal = min(max(base_payment - interest_charge, 0.0), balance)
            if regular_principal <= 0 and intended_extra <= 0:
                break
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
            fill="tozeroy", fillcolor="rgba(231,76,60,0.08)",
        ))
        if has_acceleration:
            fig_m.add_trace(go.Scatter(
                x=acc_dates_x, y=acc_balances,
                name=acc_label,
                line=dict(color="#2ecc71", width=2),
                fill="tozeroy", fillcolor="rgba(46,204,113,0.12)",
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
            xaxis_title="Year", yaxis_title="Balance ($)",
            yaxis_tickformat="$,.0f", xaxis=dict(type="date", tickformat="%Y"),
            hovermode="x unified",
        )
        if has_acceleration:
            _bal_fname = (
                f"loan-{_money_tag(loan_amount)}-payoff-{_dur_tag(months_saved)}-early"
                f"-save-{_money_tag(interest_saved)}-interest"
            )
        else:
            _bal_fname = (
                f"loan-{_money_tag(loan_amount)}-{_rate_tag(debt_rate)}pct"
                f"-{_money_tag(std_total_interest)}-interest-over-{int(debt_years)}y"
            )
        st.plotly_chart(fig_m, width='stretch', config=_png_config(_bal_fname))

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
            line=dict(color="#e74c3c", width=2),
        ))
        fig_int.add_trace(go.Scatter(
            x=acc_dates_x, y=acc_interests,
            name=acc_label,
            line=dict(color="#2ecc71", width=2),
        ))
        fig_int.update_layout(
            title="Cumulative Interest Paid Over Time",
            xaxis_title="Year", yaxis_title="Cumulative Interest ($)",
            yaxis_tickformat="$,.0f", xaxis=dict(type="date", tickformat="%Y"),
            hovermode="x unified",
        )
        _int_fname = f"interest-save-{_money_tag(interest_saved)}-payoff-{_dur_tag(months_saved)}-early"
        st.plotly_chart(fig_int, width='stretch', config=_png_config(_int_fname))

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

    std_y, std_m_rem = divmod(std_months, 12)
    with st.expander(f"Standard amortization schedule — {std_y}y {std_m_rem}m, {std_months} payments"):
        _render_schedule(std_df, include_extra_column=False)

    if has_acceleration:
        acc_y, acc_m_rem = divmod(acc_months, 12)
        with st.expander(f"Accelerated amortization schedule — {acc_label}, {acc_y}y {acc_m_rem}m, {acc_months} payments"):
            _render_schedule(acc_df, include_extra_column=True)

    st.query_params.update({
        "dLoan":      str(int(debt_loan)),
        "dRate":      f"{debt_rate:.3f}",
        "dTerm":      str(int(debt_years)),
        "dOrigMonth": str(int(orig_month)),
        "dOrigYear":  str(int(orig_year)),
        "dBiweekly":  "1" if biweekly else "0",
        "dExtra":     str(int(extra_payment)),
        "dExtraMonth": str(int(extra_start_month)),
        "dExtraYear":  str(int(extra_start_year)),
    })
    st.caption(SHARE_CAPTION)
