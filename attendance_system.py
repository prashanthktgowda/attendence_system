import streamlit as st
import qrcode
from geopy.distance import geodesic
import uuid
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import os

# Initialize session state
if "attendance_data" not in st.session_state:
    st.session_state.attendance_data = {}
if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False
if "session_code" not in st.session_state:
    st.session_state.session_code = None
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = None

# Default styles
st.markdown("""
    <style>
        .stTitle {text-align: center; color: #004466; font-size: 30px; font-weight: bold;}
        .stHeader {color: #004466; font-size: 24px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

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
    st.markdown("<div class='stHeader'>Generate Attendance QR Code</div>", unsafe_allow_html=True)

    if not st.session_state.session_active:
        subject_name = st.text_input("Enter Subject Name")
        admin_lat = st.number_input("Enter Latitude for Attendance Location", format="%.6f")
        admin_lon = st.number_input("Enter Longitude for Attendance Location", format="%.6f")
        attendance_range = st.number_input("Enter Attendance Range (in meters)", value=10)

        if st.button("Generate QR Code"):
            session_code = f"{subject_name}_{datetime.now().strftime('%Y-%m-%d')}"
            qr_data = fhttps://attendencesystem.streamlit.app//?session_code={session_code}&lat={admin_lat}&lon={admin_lon}&range={attendance_range}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            img.save("attendance_qr.png")

            st.session_state.session_active = True
            st.session_state.session_code = session_code
            st.session_state.session_start_time = datetime.now()
            st.session_state.admin_coords = (admin_lat, admin_lon)
            st.session_state.attendance_range = attendance_range
            st.session_state.attendance_data[session_code] = []

    if st.session_state.session_active:
        st.image("attendance_qr.png", caption="Scan this QR code to mark attendance")
        st.write("Session Code:", st.session_state.session_code)
        if st.button("End Session"):
            st.session_state.session_active = False
            st.session_state.session_code = None
            st.session_state.session_start_time = None
            st.rerun()
    
    st.markdown("<div class='stHeader'>Fetch Attendance Data</div>", unsafe_allow_html=True)
    fetch_code = st.text_input("Enter Session Code to Fetch Attendance")
    if st.button("Fetch Report") and fetch_code in st.session_state.attendance_data:
        df = pd.DataFrame(st.session_state.attendance_data[fetch_code])
        st.dataframe(df)
    elif fetch_code:
        st.error("No attendance data found for this session.")

# Student Interface
def student_interface():
    st.markdown("<div class='stHeader'>Mark Your Attendance</div>", unsafe_allow_html=True)
    query_params = st.query_params
    session_code = query_params.get("session_code", [None])[0]
    admin_lat = query_params.get("lat", [None])[0]
    admin_lon = query_params.get("lon", [None])[0]
    attendance_range = query_params.get("range", [None])[0]

    if session_code and admin_lat and admin_lon and attendance_range:
        st.write("You are accessing the attendance session.")
        admin_coords = (float(admin_lat), float(admin_lon))

        name = st.text_input("Enter Your Name")
        usn = st.text_input("Enter Your USN")
        
        if st.button("Confirm Attendance"):
            if session_code in st.session_state.attendance_data and not any(entry['USN'] == usn for entry in st.session_state.attendance_data[session_code]):
                st.session_state.attendance_data[session_code].append({
                    "Name": name,
                    "USN": usn,
                    "Time": datetime.now().strftime('%H:%M:%S')
                })
                st.success("Attendance Marked Successfully!")
                st.rerun()
            else:
                st.error("You have already marked attendance.")
    else:
        st.write("Please scan the QR code provided by your teacher.")

# Main App
def main():
    st.markdown("<div class='stTitle'>Advanced Attendance System</div>", unsafe_allow_html=True)
    role = st.radio("Select Role", ["Teacher", "Student"], index=0)
    
    if role == "Teacher":
        teacher_dashboard()
    else:
        student_interface()

if __name__ == "__main__":
    main()
