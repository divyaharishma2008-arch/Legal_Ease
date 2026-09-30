"""
LegalEase export helpers
========================
Utilities that turn generated document text into:
    - a plain text file (TXT)
    - a Word document (DOCX, python-docx)
    - a PDF (fpdf2)
    - a safe HTML block for the Streamlit preview

Dependencies:
    pip install python-docx fpdf2
"""

import re
from io import BytesIO
from typing import Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from fpdf import FPDF


def sanitize_text(text: str) -> str:
    """
    Make text safe for the default PDF font while preserving normal content.

    Replaces common typographic characters with ASCII equivalents, then removes
    every remaining character outside printable ASCII (tabs and newlines are
    kept). Non-English text is therefore dropped.

    Args:
        text: Raw document text.

    Returns:
        str: ASCII-only text with surrounding whitespace removed.
    """
    replacements = {
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2022": "-",   # bullet
        "\u00a0": " ",   # non-breaking space
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", text)
    return text.strip()


def format_txt(text: str) -> bytes:
    """Return the text encoded as UTF-8 bytes for the TXT download."""
    return text.encode("utf-8")


def _add_logo(doc: Document, logo_path: Optional[str]):
    """Add a centred logo to the DOCX. Silently skipped if it cannot be loaded."""
    if logo_path:
        try:
            paragraph = doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run()
            run.add_picture(logo_path, width=Inches(1.25))
        except Exception:
            pass


def format_docx(
    text: str,
    doc_type: str,
    logo_path: Optional[str] = None,
) -> bytes:
    """
    Build a Word document from the generated text.

    Layout: optional logo, centred uppercase title, one paragraph per line
    (Times New Roman 11 pt), bold headings, and a footer note.

    Args:
        text: Document body, one paragraph per line.
        doc_type: Document type used as the title.
        logo_path: Optional path to a logo image.

    Returns:
        bytes: The .docx file content.
    """
    doc = Document()

    # Page margins
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    _add_logo(doc, logo_path)

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(doc_type.upper())
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(16)

    # Body
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            doc.add_paragraph()  # blank line -> empty paragraph
            continue

        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.08

        run = p.add_run(line)
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)

        # Heading rule: short line that is uppercase, numbered, or starts
        # with a known section word.
        if (
            len(line) < 90
            and (
                line.isupper()
                or re.match(r"^\d+[\.\)]\s+", line)
                or line.lower().startswith(("important notice", "parties", "signatures"))
            )
        ):
            run.bold = True

    # Footer
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("LegalEase - AI-generated draft")
    footer_run.font.name = "Times New Roman"
    footer_run.font.size = Pt(9)

    output = BytesIO()
    doc.save(output)
    return output.getvalue()


class LegalEasePDF(FPDF):
    """FPDF subclass with a repeating header (logo + title) and footer."""

    def __init__(self, doc_type: str, logo_path: Optional[str] = None):
        super().__init__()
        self.doc_type = doc_type
        self.logo_path = logo_path

    def header(self):
        """Draw the logo (if any) and the uppercase title on every page."""
        if self.logo_path:
            try:
                self.image(self.logo_path, x=95, y=8, w=20)  # centred on A4
                self.ln(18)
            except Exception:
                pass
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, self.doc_type.upper(), align="C")
        self.ln(10)

    def footer(self):
        """Draw the footer note 15 mm from the bottom of every page."""
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 10, "LegalEase - AI-generated draft", align="C")


def format_pdf(
    text: str,
    doc_type: str,
    logo_path: Optional[str] = None,
) -> bytes:
    """
    Build a PDF from the generated text.

    The text is sanitised to ASCII first because the built-in Helvetica font
    cannot render other characters.

    Args:
        text: Document body, one paragraph per line.
        doc_type: Document type used in the page header.
        logo_path: Optional path to a logo image.

    Returns:
        bytes: The PDF file content.
    """
    pdf = LegalEasePDF(doc_type, logo_path)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    safe_text = sanitize_text(text)

    for raw_line in safe_text.splitlines():
        line = raw_line.strip()
        if not line:
            pdf.ln(4)  # blank line -> small vertical gap
            continue

        is_heading = (
            line.isupper()
            or re.match(r"^\d+[\.\)]\s+", line)
            or line.lower().startswith(("important notice", "parties", "signatures"))
        )

        if is_heading:
            pdf.set_font("Helvetica", "B", 11)
        else:
            pdf.set_font("Helvetica", "", 11)

        pdf.multi_cell(0, 6, line)
        pdf.ln(1)

    return bytes(pdf.output())


def format_html_preview(text: str) -> str:
    """
    Create safe HTML for the Streamlit preview.

    The text is HTML-escaped first, so generated content cannot inject markup.
    Blank lines become paragraphs and single line breaks become <br>.

    Args:
        text: Document text.

    Returns:
        str: HTML for st.markdown(..., unsafe_allow_html=True).
    """
    import html

    escaped = html.escape(text)
    paragraphs = []
    for block in escaped.split("\n\n"):
        block = block.replace("\n", "<br>")
        paragraphs.append(f"<p>{block}</p>")

    return f"""
    <div style="
        background:#111827;
        color:#f3f4f6;
        padding:24px;
        border-radius:14px;
        max-height:620px;
        overflow-y:auto;
        line-height:1.65;
        font-family:Georgia, 'Times New Roman', serif;
        border:1px solid #374151;">
        {''.join(paragraphs)}
    </div>
    """
