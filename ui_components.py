"""Reusable Streamlit UI components."""
from __future__ import annotations

import plotly.express as px
import streamlit as st
import pandas as pd


def metric_card(label: str, value: str):
    st.markdown(
        f"<div class='metric-card'><div style='font-size:0.8rem;color:gray'>{label}</div><div style='font-size:1.2rem;font-weight:600'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def mini_bar(values: list[float], height: int = 20):
    fig = px.bar(x=list(range(len(values))), y=values, height=height)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True)


def badge(text: str, kind: str = "success"):
    st.markdown(f"<span class='badge {kind}'>{text}</span>", unsafe_allow_html=True)


def detail_drawer(ticker: str, row: pd.Series):
    with st.expander(f"Details for {ticker}", expanded=False):
        st.write(row)
