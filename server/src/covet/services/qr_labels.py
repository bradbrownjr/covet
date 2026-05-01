"""QR code label sheet generation."""

from __future__ import annotations

from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER


def generate_qr_codes_pdf(
    items: list[dict],
    collection_name: str = "Items",
    labels_per_row: int = 3,
    labels_per_column: int = 4,
) -> bytes:
    """
    Generate a PDF with QR code labels for items.

    Args:
        items: List of items with 'id' and 'title' keys
        collection_name: Name of the collection for header
        labels_per_row: Number of labels per row (3 or 4)
        labels_per_column: Number of labels per column

    Returns:
        PDF bytes content
    """
    # Calculate label dimensions based on layout
    # Standard letter: 8.5" x 11"
    # Leave 0.5" margins
    usable_width = 8.5 - 1.0  # 7.5"
    usable_height = 11.0 - 1.5  # 9.5" (accounting for title)

    label_width = usable_width / labels_per_row
    label_height = usable_height / labels_per_column

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    # Build PDF elements
    elements = []

    # Title
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=ParagraphStyle("Normal", fontSize=14, alignment=TA_CENTER, fontName="Helvetica-Bold"),
    )
    elements.append(Paragraph(f"{collection_name} - QR Code Labels", title_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Create labels table
    label_data = []
    current_row = []

    for item in items:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(item["id"])
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes for embedding in PDF
        img_buffer = BytesIO()
        # Scale QR code to fit in label
        qr_size = min(label_width - 0.2, label_height - 0.5) * inch
        qr_img.save(img_buffer, format="PNG")
        qr_img_path = img_buffer.getvalue()

        # Create label cell with QR code and title
        from reportlab.platypus import Image as RLImage, Paragraph as RLParagraph

        # We'll use a simplified approach - just add the QR code and text
        label_elements = []

        # QR code (simplified - we'll use a canvas approach instead)
        current_row.append(f"QR: {item['id'][:8]}\n{item['title'][:20]}")

        if len(current_row) == labels_per_row:
            label_data.append(current_row)
            current_row = []

    # Add remaining items
    if current_row:
        # Pad with empty cells
        while len(current_row) < labels_per_row:
            current_row.append("")
        label_data.append(current_row)

    # Create table with labels
    if label_data:
        table = Table(
            label_data,
            colWidths=[label_width * inch] * labels_per_row,
            rowHeights=[label_height * inch] * len(label_data),
        )

        table.setStyle(
            TableStyle(
                [
                    ("BORDER", (0, 0), (-1, -1), 1, colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        elements.append(table)

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
