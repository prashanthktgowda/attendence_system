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
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Teacher Dashboard
def teacher_dashboard():
    st.sidebar.header("Teacher Dashboard")
    if not st.session_state.teacher_logged_in:
        password = st.sidebar.text_input("Enter Password", type="password")
        if password == "teacher123":  # Replace with a secure authentication system
            st.session_state.teacher_logged_in = True
        else:
            st.sidebar.error("Incorrect Password")
            return

    st.sidebar.success("Logged in as Teacher")
    st.header("Generate Attendance QR Code")

    if not st.session_state.session_active:
        admin_lat = st.number_input("Enter Latitude for Attendance Location", format="%.6f")
        admin_lon = st.number_input("Enter Longitude for Attendance Location", format="%.6f")
        attendance_range = st.number_input("Enter Attendance Range (in meters)", value=10)

        if st.button("Generate QR Code"):
            session_id = str(uuid.uuid4())
            qr_data = f"http://localhost:8501/?session_id={session_id}&lat={admin_lat}&lon={admin_lon}&range={attendance_range}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            img.save("attendance_qr.png")

            st.session_state.session_active = True
            st.session_state.session_id = session_id
            st.session_state.admin_coords = (admin_lat, admin_lon)
            st.session_state.attendance_range = attendance_range

    if st.session_state.session_active:
        st.image("attendance_qr.png", caption="Scan this QR code to mark attendance")
        st.write("Session ID:", st.session_state.session_id)
        if st.button("Create New Session"):
            st.session_state.session_active = False
            st.session_state.session_id = None
            st.session_state.attendance_data = []
            st.rerun()
    
    st.header("Real-Time Attendance Data")
    if st.session_state.attendance_data:
        df = pd.DataFrame(st.session_state.attendance_data)
        st.dataframe(df)
    else:
        st.write("No attendance data available.")

# Student Interface
def student_interface():
    st.header("Mark Your Attendance")
    query_params = st.query_params
    session_id = query_params.get("session_id", [None])[0]
    admin_lat = query_params.get("lat", [None])[0]
    admin_lon = query_params.get("lon", [None])[0]
    attendance_range = query_params.get("range", [None])[0]

    if session_id and admin_lat and admin_lon and attendance_range:
        st.write("You are accessing the attendance session.")
        admin_coords = (float(admin_lat), float(admin_lon))

        name = st.text_input("Enter Your Name")
        usn = st.text_input("Enter Your USN")
        
        if st.button("Confirm Attendance"):
            if not any(entry['USN'] == usn for entry in st.session_state.attendance_data):
                st.session_state.attendance_data.append({
                    "Session ID": session_id,
                    "Name": name,
                    "USN": usn
                })
                st.success("Attendance Marked Successfully!")
                st.rerun()
            else:
                st.error("You have already marked attendance.")
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
