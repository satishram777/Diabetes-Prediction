import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from PIL import Image as PILImage, ImageDraw

# --- Camera ---
try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

# ---------------------------
# Utility: ensure folders
# ---------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------
# Create placeholder logo if not present
# ---------------------------
def ensure_logo(logo_path):
    if os.path.exists(logo_path):
        return logo_path
    try:
        os.makedirs(os.path.dirname(logo_path), exist_ok=True)
        img = PILImage.new("RGB", (800, 240), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 180, 800, 240], fill=(14, 95, 216))
        d.text((24, 30), "HEALTH+ CLINIC", fill=(0, 0, 0))
        d.text((24, 80), "Diabetes Care Center", fill=(0, 0, 0))
        d.text((24, 130), "Diagnostic Report", fill=(0, 0, 0))
        img.save(logo_path)
    except Exception:
        pass
    return logo_path


# ---------------------------
# Generate Diabetes Report PDF
# ---------------------------
def create_diabetes_report_pdf(
    pdf_path,
    patient_info,
    metrics_table,
    prediction_result,
    probability=None,
    doctor_info=None,
    logo=None,
    photo=None,
    notes=""
):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=18*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Right", alignment=2))
    styles.add(ParagraphStyle(name="Small", fontSize=9, textColor=colors.gray))
    styles.add(ParagraphStyle(name="H1", fontSize=18, leading=22, spaceAfter=6, textColor=colors.HexColor("#0E5FD8")))

    story = []

    # Header: logo + title
    if logo and os.path.exists(logo):
        story.append(Image(logo, width=70*mm, height=22*mm))
    story.append(Paragraph("<b>Diabetes Prediction Report</b>", styles["H1"]))
    story.append(Paragraph(datetime.now().strftime("Generated on %d %b %Y, %I:%M %p"), styles["Small"]))
    story.append(Spacer(1, 6*mm))

    # Patient info
    patient_rows = [
        ["Patient Name", patient_info.get("name", "-"), "Patient ID", patient_info.get("id", "-")],
        ["Age", str(patient_info.get("age", "-")), "Gender", patient_info.get("gender", "-")],
        ["Contact", patient_info.get("contact", "-"), "Referred By", patient_info.get("referred_by", "-")]
    ]
    patient_table = Table(patient_rows, colWidths=[28*mm, 52*mm, 28*mm, 52*mm])
    patient_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.4, colors.HexColor("#D9D9D9")),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#ECECEC")),
        ("FONT", (0,0), (-1,-1), "Helvetica", 10),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 6*mm))

    # Metrics section
    story.append(Paragraph("<b>Measured / Entered Values</b>", styles["Normal"]))
    story.append(Spacer(1, 2*mm))
    story.append(metrics_table)
    story.append(Spacer(1, 6*mm))

    # Prediction badge
    not_diabetic = ("not" in prediction_result.lower())
    badge_color = colors.HexColor("#17A34A") if not_diabetic else colors.HexColor("#D7263D")
    badge_text = "NOT DIABETIC" if not_diabetic else "DIABETIC"
    badge = Table([[badge_text]], colWidths=[60*mm], rowHeights=[10*mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), badge_color),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.white),
        ("FONT", (0,0), (-1,-1), "Helvetica-Bold", 12),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOX", (0,0), (-1,-1), 0.6, badge_color),
    ]))

    prob_text = f"Model probability: {probability*100:.1f}%" if probability is not None else ""
    interp = (
        "Recommendation: Maintain healthy lifestyle, regular screening, and follow-up."
        if not_diabetic else
        "Recommendation: Consult your physician for confirmatory tests and management plan."
    )

    badge_row = Table([[badge, Paragraph(prob_text, styles["Normal"]) ]], colWidths=[70*mm, 100*mm])
    badge_row.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    story.append(badge_row)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(interp, styles["Normal"]))
    story.append(Spacer(1, 6*mm))

    # Notes
    if notes:
        story.append(Paragraph("<b>Notes</b>", styles["Normal"]))
        story.append(Spacer(1, 1*mm))
        story.append(Paragraph(notes, styles["Small"]))
        story.append(Spacer(1, 4*mm))

    # QR code
    payload = f"{patient_info.get('id','-')} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    qrobj = qr.QrCodeWidget(payload)
    bounds = qrobj.getBounds()
    w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
    d = 28*mm
    qr_d = Drawing(d, d, transform=[d/w, 0, 0, d/h, 0, 0])
    qr_d.add(qrobj)
    qr_table = Table([[qr_d, Paragraph("Scan to verify patient & timestamp", styles["Small"]) ]], colWidths=[30*mm, 140*mm])
    qr_table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    story.append(qr_table)
    story.append(Spacer(1, 6*mm))

    # Doctor block
    if doctor_info:
        dr_rows = [
            ["Doctor", doctor_info.get("name","-"), "Qualification", doctor_info.get("qual","-")],
            ["Reg. No.", doctor_info.get("reg","-"), "Signature", doctor_info.get("sign","________________")]
        ]
        dr_table = Table(dr_rows, colWidths=[28*mm, 52*mm, 28*mm, 52*mm])
        dr_table.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 0.4, colors.HexColor("#D9D9D9")),
            ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#ECECEC")),
            ("FONT", (0,0), (-1,-1), "Helvetica", 10),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(dr_table)
        story.append(Spacer(1, 4*mm))

    # Disclaimer
    story.append(Paragraph("<b>Disclaimer:</b> This is an AI-generated report and must not replace professional medical advice.", styles["Small"]))

    # Build PDF
    doc.build(story)
    print(f"✅ PDF report saved at: {pdf_path}")
