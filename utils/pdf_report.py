"""
utils/pdf_report.py - OPTIONAL PDF export (needs the `reportlab` package).
If reportlab is not installed, PDF_AVAILABLE is False and the Reports page simply
hides the PDF button; CSV download still works.
"""
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    PDF_AVAILABLE = True
except ImportError:  # pragma: no cover
    PDF_AVAILABLE = False


def dataframe_to_pdf(title, df, college_name="Smart College"):
    """Return the PDF file as bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1 * cm, rightMargin=1 * cm,
                            topMargin=1 * cm, bottomMargin=1 * cm)
    styles = getSampleStyleSheet()
    cell_style = styles["BodyText"]
    cell_style.fontSize = 7
    cell_style.leading = 9

    story = [
        Paragraph(college_name, styles["Title"]),
        Paragraph(f"{title} &nbsp;-&nbsp; generated {datetime.now():%d %b %Y %I:%M %p}", styles["Heading3"]),
        Spacer(1, 0.3 * cm),
    ]
    header = [Paragraph(f"<b>{_safe(c)}</b>", cell_style) for c in df.columns]
    body = [[Paragraph(_safe(v), cell_style) for v in row] for row in df.itertuples(index=False)]
    table = Table([header] + body, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEAFE")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


def _safe(value):
    """Escape characters that reportlab's mini-HTML would misread."""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
