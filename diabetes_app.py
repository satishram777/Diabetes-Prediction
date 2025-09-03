# diabetes_app.py
import os
import sys
import joblib
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# ---- Optional webcam support ----
try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

# ================== CONFIG ==================
OUT_DIR = "reports"
os.makedirs(OUT_DIR, exist_ok=True)

# Standard decision threshold
DECISION_THRESHOLD = 0.5

doctor_info = {
    "name": "Dr. A. Sharma",
    "qualification": "MD (Internal Medicine), Diabetologist",
    "hospital": "City Care Hospital, Delhi",
    "contact": "+91-9876543210"
}

logo_path = None  # e.g., "hospital_logo.png"

# ================== UTIL ==================
def capture_photo_via_webcam(out_path):
    if not HAS_CV2:
        print("❌ OpenCV (cv2) not available. Falling back to manual photo path.")
        return None

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use cv2.VideoCapture(0) on Linux/Mac
    if not cap.isOpened():
        print("❌ Webcam not accessible. Check camera permissions or device.")
        return None

    print("📸 Press SPACE to capture photo, ESC to skip")
    saved = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read from webcam.")
            break
        cv2.imshow("Capture Patient Photo", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            print("ℹ️ Capture skipped.")
            break
        elif key == 32:  # SPACE
            cv2.imwrite(out_path, frame)
            print(f"✅ Saved photo: {out_path}")
            saved = out_path
            break

    cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

    return saved

def safe_load(path, kind="file"):
    if not os.path.exists(path):
        print(f"❌ Required {kind} not found: {path}")
        sys.exit(1)

def format_prob(p):
    try:
        return f"{p*100:.1f}%"
    except Exception:
        return str(p)

# ================= PDF GENERATION ==================
def create_diabetes_report_pdf(
    pdf_path,
    patient_info,
    metrics_table,
    prediction_result,
    probability,
    doctor_info,
    logo=None,
    patient_photo=None,
    scanned_reports=None
):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallGray", fontSize=9, textColor=colors.gray))
    styles.add(ParagraphStyle(name="H1Blue", fontSize=18, leading=22, spaceAfter=6,
                              textColor=colors.HexColor("#0E5FD8")))

    story = []

    # Logo (optional)
    if logo and os.path.exists(logo):
        story.append(Image(logo, width=70*mm, height=22*mm))
        story.append(Spacer(1, 8))

    # Title and timestamp
    story.append(Paragraph("<b>Diabetes Prediction Report</b>", styles['H1Blue']))
    story.append(Paragraph(datetime.now().strftime("Generated on %d %b %Y, %I:%M %p"), styles["SmallGray"]))
    story.append(Spacer(1, 10))

    # Patient details
    story.append(Paragraph("<b>Patient Details</b>", styles['Heading2']))
    details = [
        ["Patient ID", patient_info.get("id", "-")],
        ["Name", patient_info.get("name", "-")],
        ["Age", patient_info.get("age", "-")],
        ["Gender", patient_info.get("gender", "-")],
        ["Contact", patient_info.get("contact", "-")],
    ]
    det_table = Table(details, colWidths=[35*mm, 120*mm])
    det_table.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.4, colors.HexColor("#D9D9D9")),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#ECECEC")),
        ("FONT", (0,0), (-1,-1), "Helvetica", 10),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    if patient_photo and os.path.exists(patient_photo):
        photo = Image(patient_photo, width=30*mm, height=30*mm)
        block = Table([[det_table, photo]], colWidths=[155*mm, 30*mm])
        story.append(block)
    else:
        story.append(det_table)

    story.append(Spacer(1, 10))

    # Metrics table
    story.append(Paragraph("<b>Medical Metrics</b>", styles['Heading2']))
    tbl = Table(metrics_table, colWidths=[60*mm, 40*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    # Prediction
    story.append(Paragraph("<b>Prediction Result</b>", styles['Heading2']))
    story.append(Paragraph(prediction_result, styles['Normal']))
    story.append(Paragraph(f"Decision Threshold: {int(DECISION_THRESHOLD*100)}%", styles['SmallGray']))
    story.append(Spacer(1, 12))

    # Doctor block
    story.append(Paragraph("<b>Certified By</b>", styles['Heading2']))
    story.append(Paragraph(f"Doctor: {doctor_info['name']}", styles['Normal']))
    story.append(Paragraph(f"Qualification: {doctor_info['qualification']}", styles['Normal']))
    story.append(Paragraph(f"Hospital: {doctor_info['hospital']}", styles['Normal']))
    story.append(Paragraph(f"Contact: {doctor_info['contact']}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Scanned reports
    if scanned_reports:
        story.append(PageBreak())
        story.append(Paragraph("<b>Attached Scanned Reports</b>", styles['Heading2']))
        for report in scanned_reports:
            if os.path.exists(report):
                story.append(Image(report, width=160*mm, height=120*mm))
                story.append(Spacer(1, 8))

    # Footer note
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Disclaimer: This is an AI-assisted report and should not replace professional medical advice.",
        styles["SmallGray"]
    ))

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=18*mm, bottomMargin=15*mm
    )
    doc.build(story)
    print(f"✅ Report generated and saved at {pdf_path}")

# ================= MAIN ==================
if __name__ == "__main__":
    # --- Patient info ---
    patient_info = {}
    patient_info["id"] = input("Enter Patient ID: ").strip()
    patient_info["name"] = input("Enter Patient Name: ").strip()
    patient_info["age"] = input("Enter Age: ").strip()
    patient_info["gender"] = input("Enter Gender: ").strip()
    patient_info["contact"] = input("Enter Contact Number: ").strip()

    # --- Patient photo ---
    patient_photo = None
    try:
        use_cam = input("Capture patient photo with webcam? (y/n): ").strip().lower()
    except Exception:
        use_cam = "n"

    if use_cam == "y":
        out_photo = os.path.join(OUT_DIR, f"{patient_info['id']}_photo.jpg")
        patient_photo = capture_photo_via_webcam(out_photo)
    if not patient_photo:
        manual = input("Enter path to patient photo (leave blank to skip): ").strip()
        patient_photo = manual if manual else None

    # --- Metrics ---
    def _float_in(msg):
        return float(input(msg).strip())

    def _int_in(msg):
        return int(input(msg).strip())

    pregnancies = _int_in("Pregnancies: ")
    glucose     = _int_in("Glucose: ")
    bp          = _int_in("Blood Pressure: ")
    skin        = _int_in("Skin Thickness: ")
    insulin     = _int_in("Insulin: ")
    bmi         = _float_in("BMI: ")
    dpf         = _float_in("Diabetes Pedigree Function: ")
    age_val     = int(patient_info["age"])

    metrics_table = [
        ["Metric", "Value"],
        ["Pregnancies", pregnancies],
        ["Glucose", glucose],
        ["Blood Pressure", bp],
        ["Skin Thickness", skin],
        ["Insulin", insulin],
        ["BMI", bmi],
        ["Diabetes Pedigree Function", dpf],
        ["Age", age_val]
    ]

    # --- Load model/scaler ---
    safe_load("diabetes_model.pkl", "model")
    safe_load("scaler.pkl", "scaler")
    model = joblib.load("diabetes_model.pkl")
    scaler = joblib.load("scaler.pkl")

    # --- Prepare & scale features ---
    features = [[pregnancies, glucose, bp, skin, insulin, bmi, dpf, age_val]]
    features_scaled = scaler.transform(features)

    # --- Predict ---
    proba = model.predict_proba(features_scaled)[0][1]

    if proba >= 0.6:
        prediction_result = f"The person is LIKELY Diabetic (Probability: {format_prob(proba)})"
    elif proba <= 0.4:
        prediction_result = f"The person is NOT Diabetic (Probability: {format_prob(proba)})"
    else:
        prediction_result = (
            f"Borderline case (Probability: {format_prob(proba)}). "
            "Further medical tests are recommended."
        )

    # --- Collect scanned reports (optional) ---
    scanned_reports = []
    while True:
        rep = input("Enter path of scanned report image (blank to finish): ").strip()
        if not rep:
            break
        if os.path.exists(rep):
            scanned_reports.append(rep)
        else:
            print("⚠️ File not found, skipped.")

    # --- Generate PDF ---
    pdf_path = os.path.join(OUT_DIR, f"diabetes_report_{patient_info['id']}.pdf")
    create_diabetes_report_pdf(
        pdf_path=pdf_path,
        patient_info=patient_info,
        metrics_table=metrics_table,
        prediction_result=prediction_result,
        probability=proba,
        doctor_info=doctor_info,
        logo=logo_path,
        patient_photo=patient_photo,
        scanned_reports=scanned_reports
    )
