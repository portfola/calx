import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Investment Calculator", page_icon="📈", layout="wide")

st.title("Investment Calculator")
st.markdown("Plan and visualize your investment growth over time.")

tab1, tab2, tab3 = st.tabs(["Compound Interest", "SIP / Regular Contributions", "Goal Planner"])

# --- Tab 1: Compound Interest ---
with tab1:
    st.header("Compound Interest Calculator")

    col1, col2 = st.columns([1, 2])

    with col1:
        principal = st.number_input("Initial Investment ($)", min_value=0, value=10000, step=500)
        annual_rate = st.slider("Annual Return Rate (%)", min_value=0.0, max_value=30.0, value=7.0, step=0.1)
        years = st.slider("Investment Period (Years)", min_value=1, max_value=50, value=20)
        compounds_per_year = st.selectbox(
            "Compounding Frequency",
            options=[1, 4, 12, 365],
            format_func=lambda x: {1: "Annually", 4: "Quarterly", 12: "Monthly", 365: "Daily"}[x],
            index=2,
        )

    r = annual_rate / 100 / compounds_per_year
    n_periods = years * compounds_per_year
    year_range = np.arange(0, years + 1)
    balances = [principal * (1 + r) ** (compounds_per_year * y) for y in year_range]
    final_value = balances[-1]
    total_gain = final_value - principal

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=year_range, y=balances, mode="lines", name="Balance", fill="tozeroy", line=dict(color="#2ecc71", width=2)))
        fig.add_trace(go.Scatter(x=year_range, y=[principal] * len(year_range), mode="lines", name="Principal", line=dict(color="#95a5a6", dash="dash")))
        fig.update_layout(title="Portfolio Growth", xaxis_title="Years", yaxis_title="Value ($)", yaxis_tickformat="$,.0f", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

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
        st.plotly_chart(fig2, use_container_width=True)

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
        st.plotly_chart(fig3, use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Required Monthly Contribution", f"${max(required_monthly, 0):,.2f}")
    m2.metric("Growth from Initial Investment", f"${future_principal:,.2f}")
    m3.metric("Needed from Contributions", f"${max(remaining, 0):,.2f}")
