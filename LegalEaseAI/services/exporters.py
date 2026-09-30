from __future__ import annotations

import html
import re

from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
)


BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_LOGO_PATH = (
    BASE_DIR / "assets" / "legalese_logo.png"
)


# --------------------------------------------------
# TEXT CLEANING
# --------------------------------------------------

def sanitize_text(text: str) -> str:

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
        "\u2022": "-",
        "\ufeff": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


def _lines(text: str) -> list[str]:

    return [
        line.strip()
        for line in sanitize_text(text).splitlines()
        if line.strip()
    ]


def _looks_like_heading(line: str) -> bool:

    upper = line.upper()

    return (
        len(line) <= 100
        and (
            bool(
                re.match(
                    r"^\d+[\.\)]\s+",
                    line
                )
            )
            or upper in {
                "BETWEEN",
                "AND",
                "SIGNATURES",
                "DISCLAIMER",
                "DRAFT DOCUMENT",
            }
            or (
                line.isupper()
                and len(line.split()) <= 12
            )
        )
    )


# --------------------------------------------------
# HTML PREVIEW
# --------------------------------------------------

def format_html_preview(text: str) -> str:

    blocks = []

    for line in _lines(text):

        escaped = html.escape(line)

        if _looks_like_heading(line):

            blocks.append(
                f'<h3 class="legal-heading">'
                f'{escaped}'
                f'</h3>'
            )

        elif re.match(r"^[-*]\s+", line):

            blocks.append(
                f'<li>{html.escape(line[2:].strip())}</li>'
            )

        else:

            blocks.append(
                f"<p>{escaped}</p>"
            )

    return "\n".join(blocks)


# --------------------------------------------------
# DOCX EXPORT
# --------------------------------------------------

def format_docx(
    text: str,
    doc_type: str,
    logo_path: str | Path = DEFAULT_LOGO_PATH,
) -> bytes:

    document = Document()

    section = document.sections[0]

    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    normal = document.styles["Normal"]

    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)

    # Logo temporarily disabled to avoid image errors.

    title = document.add_paragraph()

    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = title.add_run(doc_type.upper())

    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(16)

    for line in _lines(text):

        if line.upper() == doc_type.upper():
            continue

        if _looks_like_heading(line):

            paragraph = document.add_paragraph()

            paragraph.paragraph_format.space_before = Pt(8)

            heading = paragraph.add_run(line)

            heading.bold = True
            heading.font.name = "Times New Roman"
            heading.font.size = Pt(12)

        else:

            paragraph = document.add_paragraph()

            paragraph.paragraph_format.space_after = Pt(5)

            paragraph.add_run(line)

    footer = section.footer.paragraphs[0]

    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    footer_run = footer.add_run(
        "LegalEase - AI-generated draft. "
        "Review with a qualified legal professional "
        "before use."
    )

    footer_run.italic = True

    output = BytesIO()

    document.save(output)

    return output.getvalue()


# --------------------------------------------------
# PDF EXPORT
# --------------------------------------------------

def format_pdf(
    text: str,
    doc_type: str,
    logo_path: str | Path = DEFAULT_LOGO_PATH,
) -> bytes:

    buffer = BytesIO()

    class LegalDocTemplate(BaseDocTemplate):
        pass

    def header_footer(canvas, doc):

        canvas.saveState()

        width, height = A4

        # Logo temporarily disabled to avoid image errors.

        canvas.setFont("Helvetica", 8)

        canvas.drawCentredString(
            width / 2,
            10 * mm,
            (
                f"LegalEase | Page {doc.page} | "
                "AI-generated draft; "
                "legal review recommended"
            ),
        )

        canvas.restoreState()

    document = LegalDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=30 * mm,
        bottomMargin=18 * mm,
        title=f"LegalEase - {doc_type}",
        author="LegalEase",
    )

    frame = Frame(
        document.leftMargin,
        document.bottomMargin,
        document.width,
        document.height,
        id="normal",
    )

    document.addPageTemplates(
        [
            PageTemplate(
                id="legal",
                frames=frame,
                onPage=header_footer,
            )
        ]
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "LegalTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "LegalHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14,
        spaceBefore=8,
        spaceAfter=5,
    )

    body_style = ParagraphStyle(
        "LegalBody",
        parent=styles["BodyText"],
        alignment=TA_LEFT,
        fontName="Times-Roman",
        fontSize=10.5,
        leading=14,
        spaceAfter=6,
    )

    story = [
        Paragraph(
            html.escape(doc_type.upper()),
            title_style,
        )
    ]

    for line in _lines(text):

        if line.upper() == doc_type.upper():
            continue

        safe = html.escape(line)

        if _looks_like_heading(line):

            story.append(
                Paragraph(
                    safe,
                    heading_style,
                )
            )

        elif re.match(r"^[-*]\s+", line):

            story.append(
                Paragraph(
                    "&#8226; "
                    + html.escape(line[2:].strip()),
                    body_style,
                )
            )

        else:

            story.append(
                Paragraph(
                    safe,
                    body_style,
                )
            )

    document.build(story)

    return buffer.getvalue()


# --------------------------------------------------
# TXT EXPORT
# --------------------------------------------------

def format_txt(text: str) -> bytes:

    return sanitize_text(text).encode("utf-8")