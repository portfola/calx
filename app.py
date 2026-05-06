import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Investment Calculator", page_icon="📈", layout="wide")

st.title("Investment Calculator")
st.markdown("Plan and visualize your investment growth over time.")

tab1, tab2, tab3, tab4 = st.tabs(["Compound Interest", "SIP / Regular Contributions", "Goal Planner", "Mortgage Calculator"])

# --- Tab 1: Compound Interest ---
with tab1:
    st.header("Compound Interest Calculator")

    col1, col2 = st.columns([1, 2])

    with col1:
        principal = st.number_input("Initial Investment ($)", min_value=0, value=10000, step=500)
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
with tab2:
    st.header("SIP / Regular Contribution Calculator")

    col1, col2 = st.columns([1, 2])

    with col1:
        sip_principal = st.number_input("Initial Investment ($)", min_value=0, value=5000, step=500, key="sip_principal")
        monthly_contrib = st.number_input("Monthly Contribution ($)", min_value=0, value=500, step=50)
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
with tab3:
    st.header("Goal Planner")
    st.markdown("Find out how much to invest monthly to reach a target.")

    col1, col2 = st.columns([1, 2])

    with col1:
        goal_amount = st.number_input("Target Amount ($)", min_value=1000, value=500000, step=10000)
        goal_initial = st.number_input("Initial Investment ($)", min_value=0, value=10000, step=1000)
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
with tab4:
    st.header("Mortgage Calculator")
    st.markdown("See how much interest you pay over the life of your loan — and how much you can save by paying extra principal each month.")

    col1, col2 = st.columns([1, 2])

    with col1:
        home_price = st.number_input("Home Price ($)", min_value=10000, value=400000, step=5000)
        down_pct = st.slider("Down Payment (%)", min_value=0, max_value=50, value=20, step=1)
        mort_rate = st.slider("Annual Interest Rate (%)", min_value=0.1, max_value=15.0, value=6.75, step=0.05)
        mort_years = st.selectbox("Loan Term (Years)", options=[10, 15, 20, 25, 30], index=4)
        extra_payment = st.number_input("Extra Monthly Principal ($)", min_value=0, value=0, step=50,
                                        help="Additional amount paid toward principal each month on the accelerated schedule")

    down_amount = home_price * down_pct / 100
    loan_amount = home_price - down_amount
    monthly_rate = mort_rate / 100 / 12
    n_payments = mort_years * 12

    if monthly_rate > 0:
        monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** n_payments / ((1 + monthly_rate) ** n_payments - 1)
    else:
        monthly_payment = loan_amount / n_payments

    def amortize(loan, monthly_rate, base_payment, extra=0):
        """Return lists of (balance, cumulative_interest) month by month."""
        balance = loan
        cum_interest = 0.0
        balances = [balance]
        interests = [0.0]
        while balance > 0:
            interest_charge = balance * monthly_rate
            principal_charge = min(base_payment - interest_charge + extra, balance)
            if principal_charge <= 0:
                break
            cum_interest += interest_charge
            balance -= principal_charge
            balances.append(max(balance, 0))
            interests.append(cum_interest)
        return balances, interests

    std_balances, std_interests = amortize(loan_amount, monthly_rate, monthly_payment, extra=0)
    acc_balances, acc_interests = amortize(loan_amount, monthly_rate, monthly_payment, extra=extra_payment)

    std_months = len(std_balances) - 1
    acc_months = len(acc_balances) - 1
    std_total_interest = std_interests[-1]
    acc_total_interest = acc_interests[-1]
    interest_saved = std_total_interest - acc_total_interest
    months_saved = std_months - acc_months

    std_years_x = [m / 12 for m in range(std_months + 1)]
    acc_years_x = [m / 12 for m in range(acc_months + 1)]

    with col2:
        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(
            x=std_years_x, y=std_balances,
            name="Standard schedule",
            line=dict(color="#e74c3c", width=2),
            fill="tozeroy", fillcolor="rgba(231,76,60,0.08)"
        ))
        if extra_payment > 0:
            fig_m.add_trace(go.Scatter(
                x=acc_years_x, y=acc_balances,
                name=f"Accelerated (+${extra_payment:,}/mo)",
                line=dict(color="#2ecc71", width=2),
                fill="tozeroy", fillcolor="rgba(46,204,113,0.12)"
            ))
        fig_m.update_layout(
            title="Remaining Loan Balance Over Time",
            xaxis_title="Years",
            yaxis_title="Balance ($)",
            yaxis_tickformat="$,.0f",
            hovermode="x unified"
        )
        st.plotly_chart(fig_m, width='stretch')

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Loan Amount", f"${loan_amount:,.0f}")
    m2.metric("Monthly Payment", f"${monthly_payment:,.2f}")
    m3.metric("Total Interest (Standard)", f"${std_total_interest:,.0f}")
    if extra_payment > 0:
        m4.metric("Interest Saved", f"${interest_saved:,.0f}", delta=f"-{months_saved} months")
    else:
        m4.metric("Total Cost", f"${loan_amount + std_total_interest:,.0f}")

    st.divider()

    if extra_payment > 0:
        st.subheader("Payoff Comparison")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Standard Payoff", f"{std_months // 12}y {std_months % 12}m")
        c2.metric("Accelerated Payoff", f"{acc_months // 12}y {acc_months % 12}m")
        c3.metric("Time Saved", f"{months_saved // 12}y {months_saved % 12}m")
        c4.metric("Interest Saved", f"${interest_saved:,.0f}")

        fig_int = go.Figure()
        fig_int.add_trace(go.Scatter(
            x=std_years_x, y=std_interests,
            name="Standard schedule",
            line=dict(color="#e74c3c", width=2)
        ))
        fig_int.add_trace(go.Scatter(
            x=acc_years_x, y=acc_interests,
            name=f"Accelerated (+${extra_payment:,}/mo)",
            line=dict(color="#2ecc71", width=2)
        ))
        fig_int.update_layout(
            title="Cumulative Interest Paid Over Time",
            xaxis_title="Years",
            yaxis_title="Cumulative Interest ($)",
            yaxis_tickformat="$,.0f",
            hovermode="x unified"
        )
        st.plotly_chart(fig_int, width='stretch')

    with st.expander("Show amortization table (standard schedule, first 24 months)"):
        rows = []
        bal = loan_amount
        for mo in range(1, min(25, std_months + 1)):
            interest_charge = bal * monthly_rate
            principal_charge = monthly_payment - interest_charge
            bal = max(bal - principal_charge, 0)
            rows.append({"Month": mo, "Payment": f"${monthly_payment:,.2f}",
                         "Principal": f"${principal_charge:,.2f}",
                         "Interest": f"${interest_charge:,.2f}",
                         "Balance": f"${bal:,.2f}"})
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
