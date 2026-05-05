# calx — Financial Calculator Dashboard

A Streamlit dashboard for planning investments and understanding mortgage costs.

## Features

- **Compound Interest** — Calculate growth from a lump-sum investment with configurable compounding frequency (annual, quarterly, monthly, daily)
- **SIP / Regular Contributions** — Model portfolio growth with recurring monthly contributions on top of an initial investment
- **Goal Planner** — Work backwards from a target amount to find the required monthly contribution at a given return rate
- **Mortgage Calculator** — Calculate monthly payments and total interest over the life of a loan; compare a standard repayment schedule against an accelerated one (extra principal per month) to see exactly how much interest and time you save by paying down principal faster

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

```bash
git clone https://github.com/portfola/calx.git
cd calx
pip install -r requirements.txt
```

### Running the app

```bash
streamlit run app.py
```

The dashboard opens automatically in your browser at `http://localhost:8501`.

## Tech Stack

- [Streamlit](https://streamlit.io/) — dashboard framework
- [Plotly](https://plotly.com/python/) — interactive charts
- [Pandas](https://pandas.pydata.org/) / [NumPy](https://numpy.org/) — data handling
