import streamlit as st
import qrcode
from geopy.distance import geodesic
import uuid
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import os

# Initialize session state
if "attendance_data" not in st.session_state:
    st.session_state.attendance_data = []
if "qr_code_generated" not in st.session_state:
    st.session_state.qr_code_generated = False
if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False

# Teacher Dashboard
def teacher_dashboard():
    st.sidebar.header("Teacher Dashboard")
    if not st.session_state.teacher_logged_in:
        password = st.sidebar.text_input("Enter Password", type="password")
        if password == "teacher123":  # Replace with a secure password hashing mechanism
            st.session_state.teacher_logged_in = True
        else:
            st.sidebar.error("Incorrect Password")
            return

    if st.session_state.teacher_logged_in:
        st.sidebar.success("Logged in as Teacher")
        st.header("Generate Attendance QR Code")

        # Input GPS coordinates and range
        admin_lat = st.number_input("Enter Latitude for Attendance Location", format="%.6f")
        admin_lon = st.number_input("Enter Longitude for Attendance Location", format="%.6f")
        attendance_range = st.number_input("Enter Attendance Range (in meters)", value=2)

        if st.button("Generate QR Code"):
            # Generate a unique session ID
            session_id = str(uuid.uuid4())
            qr_data = f"https://attendencesystem.streamlit.app/?session_id={session_id}&lat={admin_lat}&lon={admin_lon}&range={attendance_range}"
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            img.save("attendance_qr.png")

            st.session_state.qr_code_generated = True
            st.session_state.session_id = session_id
            st.session_state.admin_coords = (admin_lat, admin_lon)
            st.session_state.attendance_range = attendance_range

        if st.session_state.qr_code_generated:
            st.image("attendance_qr.png", caption="Scan this QR code to mark attendance")
            st.write("Session ID:", st.session_state.session_id)

        # View real-time attendance data
        st.header("Real-Time Attendance Data")
        if st.session_state.attendance_data:
            df = pd.DataFrame(st.session_state.attendance_data)
            st.write(df)

            # Download attendance data as PDF
            if st.button("Download Attendance as PDF"):
                pdf_filename = "attendance_report.pdf"
                pdf = SimpleDocTemplate(pdf_filename, pagesize=letter)
                table_data = [df.columns.to_list()] + df.values.tolist()
                table = Table(table_data)
                style = TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), "#77DDFF"),
                    ("TEXTCOLOR", (0, 0), (-1, 0), "#000000"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), "#FFFFFF"),
                    ("GRID", (0, 0), (-1, -1), 1, "#000000"),
                ])
                table.setStyle(style)
                pdf.build([table])
                st.success(f"PDF generated: {pdf_filename}")
                with open(pdf_filename, "rb") as f:
                    st.download_button("Download PDF", f, file_name=pdf_filename)
        else:
            st.write("No attendance data available.")

# Student Interface
def student_interface():
    st.header("Mark Your Attendance")

    # Get session details from query parameters
    query_params = st.query_params
    session_id = query_params.get("session_id", [None])[0]
    admin_lat = query_params.get("lat", [None])[0]
    admin_lon = query_params.get("lon", [None])[0]
    attendance_range = query_params.get("range", [None])[0]

    if session_id and admin_lat and admin_lon and attendance_range:
        st.write("You are accessing the attendance session.")
        admin_coords = (float(admin_lat), float(admin_lon))

        # Fetch user's location using browser geolocation
        st.write("Please allow access to your location to mark attendance.")
        user_lat = st.number_input("Enter Your Latitude", format="%.6f")
        user_lon = st.number_input("Enter Your Longitude", format="%.6f")
        user_coords = (user_lat, user_lon)

        # Check if the user is within the allowed range
        distance = geodesic(admin_coords, user_coords).meters
        if distance <= float(attendance_range):
            st.success("You are within the allowed range!")

            # Input name and USN
            name = st.text_input("Enter Your Name")
            usn = st.text_input("Enter Your USN")

            if st.button("Mark Attendance"):
                # Check if the device has already marked attendance
                if "device_id" not in st.session_state:
                    st.session_state.device_id = str(uuid.uuid4())  # Simulate a unique device ID
                    st.session_state.attendance_data.append({
                        "Session ID": session_id,
                        "Name": name,
                        "USN": usn,
                        "Latitude": user_lat,
                        "Longitude": user_lon,
                        "Device ID": st.session_state.device_id
                    })
                    st.success("Attendance Marked Successfully!")
                else:
                    st.error("You have already marked attendance from this device.")
        else:
            st.error(f"You are not within the allowed range ({attendance_range} meters).")
    else:
        st.write("Please scan the QR code provided by your teacher.")

# Main App
def main():
    st.title("Advanced Attendance System")
    role = st.radio("Select Role", ["Teacher", "Student"])

    if role == "Teacher":
        teacher_dashboard()
    else:
        student_interface()

if __name__ == "__main__":
    main()
