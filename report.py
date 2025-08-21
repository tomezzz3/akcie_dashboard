"""PDF export utilities."""
from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
from datetime import datetime


def export_pdf(df: pd.DataFrame, path: str) -> str:
    """Export top picks to a simple PDF."""
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)
    c.drawString(30, height - 30, f"ValueRadar Top Picks - {datetime.now():%Y-%m-%d}")
    y = height - 60
    for _, row in df.iterrows():
        c.drawString(40, y, f"{row['ticker']} - Composite {row['Composite']:.1f}")
        y -= 20
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()
    return path


__all__ = ['export_pdf']
