import streamlit as st
import time
import geopy.distance
import qrcode
import io
import hashlib
import pandas as pd
import schedule
import threading
import os
from datetime import datetime, timedelta
from fpdf import FPDF
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from streamlit_js_eval import get_geolocation, streamlit_js_eval
import base64

# Constants
QR_VALIDITY_MINUTES = 15  # QR code expiration time
ALLOWED_RADIUS_METERS = 50  # Default attendance radius
ATTENDANCE_CSV = "attendance_records.csv"  # File to store attendance data

# Initialize session state
if "attendance_data" not in st.session_state:
    if os.path.exists(ATTENDANCE_CSV):
        st.session_state.attendance_data = pd.read_csv(ATTENDANCE_CSV)
    else:
        st.session_state.attendance_data = pd.DataFrame(columns=["name", "usn", "timestamp", "device_id", "latitude", "longitude"])

if "qr_session" not in st.session_state:
    st.session_state.qr_session = None

if "admin_email" not in st.session_state:
    st.session_state.admin_email = ""

if "allowed_radius" not in st.session_state:
    st.session_state.allowed_radius = ALLOWED_RADIUS_METERS

# Security: Use Streamlit secrets for sensitive data
SENDGRID_API_KEY = st.secrets.get("SENDGRID_API_KEY", "")
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "attendance@example.com")

# Page Title
st.title("QR Code Attendance System v3.0")

# Device Fingerprinting
def get_device_id():
    """Generate a unique device ID using browser characteristics."""
    try:
        client_info = streamlit_js_eval(js_expressions='''navigator.userAgent + 
            screen.width + screen.height + navigator.platform''')
        return hashlib.sha256(client_info.encode()).hexdigest()[:16]
    except:
        return "unknown_device"

# Enhanced Location Fetching
def get_location():
    """Fetch the user's current location using browser geolocation."""
    try:
        loc = get_geolocation()
        if loc and 'coords' in loc:
            return (loc['coords']['latitude'], loc['coords']['longitude'])
        return None
    except Exception as e:
        st.error(f"Error fetching location: {str(e)}")
        return None

# QR Code Generation with Session Management
def generate_qr_session(location, radius):
    """Generate a new QR session with a unique ID and expiration time."""
    session_id = hashlib.sha256(f"{datetime.now()}{location}".encode()).hexdigest()[:8]
    expires = datetime.now() + timedelta(minutes=QR_VALIDITY_MINUTES)
    return {
        'id': session_id,
        'location': location,
        'radius': radius,
        'expires': expires,
        'qr_generated': datetime.now()
    }

# Attendance Validation
def validate_attendance(student_loc, device_id):
    """Validate the student's attendance based on location and device ID."""
    if not st.session_state.qr_session:
        return False, "No active attendance session"
    
    session = st.session_state.qr_session
    if datetime.now() > session['expires']:
        return False, "QR Code expired"
    
    distance = geopy.distance.geodesic(session['location'], student_loc).meters
    if distance > session['radius']:
        return False, f"Location mismatch ({distance:.1f}m from class)"
    
    existing = st.session_state.attendance_data[
        (st.session_state.attendance_data['device_id'] == device_id) &
        (st.session_state.attendance_data['timestamp'] >= (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"))
    ]
    if not existing.empty:
        return False, "Attendance already recorded today"
    
    return True, "Validated"

# Generate PDF Report
def generate_pdf_report():
    """Generate a PDF report of attendance records."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Attendance Report", ln=True, align="C")
    pdf.ln(10)
    
    # Session Info
    pdf.set_font("Arial", "", 12)
    if st.session_state.qr_session:
        session = st.session_state.qr_session
        pdf.cell(0, 10, f"Session ID: {session['id']}", ln=True)
        pdf.cell(0, 10, f"Location: {session['location'][0]:.6f}, {session['location'][1]:.6f}", ln=True)
        pdf.cell(0, 10, f"Radius: {session['radius']} meters", ln=True)
        pdf.cell(0, 10, f"Valid Until: {session['expires'].strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)
    
    # Attendance Data
    pdf.set_font("Arial", "B", 12)
    cols = ["Name", "USN", "Timestamp", "Device ID"]
    col_widths = [45, 45, 50, 60]
    
    for col, width in zip(cols, col_widths):
        pdf.cell(width, 10, col, border=1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for _, row in st.session_state.attendance_data.iterrows():
        pdf.cell(col_widths[0], 10, row['name'][:15])
        pdf.cell(col_widths[1], 10, row['usn'][:15])
        pdf.cell(col_widths[2], 10, row['timestamp'][:19])
        pdf.cell(col_widths[3], 10, row['device_id'][:15])
        pdf.ln()
    
    pdf_bytes = io.BytesIO()
    pdf.output(pdf_bytes, "F")
    return pdf_bytes.getvalue()

# Email Service with Error Handling
def send_email_report():
    """Send an email with the attendance report as a PDF attachment."""
    if not st.session_state.admin_email:
        return
    
    try:
        pdf_data = generate_pdf_report()
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=st.session_state.admin_email,
            subject=f"Attendance Report - {datetime.now().strftime('%Y-%m-%d')}",
            html_content="<strong>Attendance report attached</strong>"
        )
        
        encoded = base64.b64encode(pdf_data).decode()
        attachment = Attachment(
            FileContent(encoded),
            FileName(f"attendance_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"),
            FileType("application/pdf"),
            Disposition("attachment")
        )
        message.attachment = attachment
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        if response.status_code == 202:
            st.sidebar.success("Report sent successfully!")
        else:
            st.sidebar.error(f"Email failed: {response.body}")
    except Exception as e:
        st.sidebar.error(f"Email error: {str(e)}")

# Admin Interface
st.sidebar.header("Admin Settings")

# Attendance Session Setup
st.sidebar.subheader("Attendance Session Setup")
admin_latlon = get_location()
if admin_latlon:
    st.sidebar.success(f"Detected Location: {admin_latlon[0]:.6f}, {admin_latlon[1]:.6f}")

st.session_state.allowed_radius = st.sidebar.slider(
    "Allowed Radius (meters)",
    10, 500, ALLOWED_RADIUS_METERS
)

if st.sidebar.button("Start New Attendance Session"):
    if admin_latlon:
        st.session_state.qr_session = generate_qr_session(admin_latlon, st.session_state.allowed_radius)
        qr_data = f"{st.session_state.qr_session['id']}|{admin_latlon[0]}|{admin_latlon[1]}|{st.session_state.allowed_radius}"
        qr = qrcode.make(qr_data)
        img_bytes = io.BytesIO()
        qr.save(img_bytes, format="PNG")
        st.sidebar.image(img_bytes.getvalue(), caption=f"Session ID: {st.session_state.qr_session['id']}")
        st.sidebar.info(f"QR valid until: {st.session_state.qr_session['expires'].strftime('%H:%M:%S')}")
    else:
        st.sidebar.error("Could not determine location")

# Email Settings
st.sidebar.subheader("Email Settings")
st.session_state.admin_email = st.sidebar.text_input("Report Email", st.session_state.admin_email)

if st.sidebar.button("Send Report Now"):
    send_email_report()

# Student Interface
st.header("Mark Attendance")
name = st.text_input("Full Name").strip()
usn = st.text_input("Student ID").strip().upper()

if st.button("Get Location & Submit"):
    device_id = get_device_id()
    student_loc = get_location()
    
    if not student_loc:
        st.error("Location access required")
        
    
    valid, message = validate_attendance(student_loc, device_id)
    
    if valid:
        new_entry = {
            "name": name,
            "usn": usn,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "device_id": device_id,
            "latitude": student_loc[0],
            "longitude": student_loc[1]
        }
        st.session_state.attendance_data = pd.concat([
            st.session_state.attendance_data,
            pd.DataFrame([new_entry])
        ], ignore_index=True)
        st.session_state.attendance_data.to_csv(ATTENDANCE_CSV, index=False)  # Save to CSV
        st.success("Attendance recorded successfully!")
    else:
        st.error(f"Validation failed: {message}")

# Live Attendance Display
st.header("Live Attendance")
st.dataframe(
    st.session_state.attendance_data.sort_values("timestamp", ascending=False),
    use_container_width=True,
    hide_index=True
)

# Scheduled tasks
schedule.every(30).minutes.do(send_email_report)

def scheduler_thread():
    """Background thread for scheduled tasks."""
    while True:
        schedule.run_pending()
        time.sleep(60)

if not hasattr(st.session_state, 'scheduler_running'):
    st.session_state.scheduler_running = True
    threading.Thread(target=scheduler_thread, daemon=True).start()