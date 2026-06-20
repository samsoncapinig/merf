# 🔹 1. IMPORTS (top of file)
import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import smtplib
from email.mime.text import MIMEText

# 🔹 2. GOOGLE DRIVE FUNCTION (put it HERE ✅)

def get_drive_service():
    SCOPES = ['https://www.googleapis.com/auth/drive']

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)

    service = build('drive', 'v3', credentials=creds)
    return service
def save_to_google_sheet(data):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)

    client = gspread.authorize(creds)

    sheet = client.open("MERF Responses").sheet1

    sheet.append_row(data)    
# 🔹 3. UPLOAD FUNCTION (below it ✅)

def upload_to_drive(file, filename):
    service = get_drive_service()

    file_metadata = {
        'name': filename,
        'parents': ['1gHafPfK31w9nQ3siyVW4BpbsCs7VVS_X']  # ✅ fixed
    }

    file_stream = io.BytesIO(file.getbuffer())

    media = MediaIoBaseUpload(file_stream, mimetype=file.type)

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded.get('id')

    # ✅ create link
    file_link = f"https://drive.google.com/file/d/{file_id}/view"

    return file_link

def send_email_notification(data):
    sender = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]

    # ✅ multiple recipients
    recipients = st.secrets["EMAIL_TO"].split(",")

    subject = "New MERF Submission"

    body = f"""
New MERF Submission Received:

Program Owner: {data['Program Owner']}
Training Title: {data['Training Title']}
Venue: {data['Venue']}
Dates: {data['Dates']}
QAME: {data['QAME']}

Participants:
Teaching: {data['Teaching']}
Non-Teaching: {data['Non-Teaching']}
Teaching Related: {data['Teaching Related']}

Files:
Signed Memorandum: {data['Memo Link']}
Activity Matrix: {data['Matrix Link']}
"""

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)

# 🔹 4. SUBMIT BUTTON (below it ✅)
if st.button("Submit MERF"):

    memo_link = ""
    matrix_link = ""

    if memo_file:
        memo_link = upload_to_drive(memo_file, memo_file.name)

    if matrix_file:
        matrix_link = upload_to_drive(matrix_file, matrix_file.name)

    # ✅ Data dictionary for email
    data_dict = {
        "Program Owner": program_owner,
        "Training Title": training_title,
        "Venue": venue,
        "Dates": str(dates),
        "QAME": qame_other,
        "Teaching": teaching,
        "Non-Teaching": non_teaching,
        "Teaching Related": teaching_related,
        "Memo Link": memo_link,
        "Matrix Link": matrix_link
    }

    # ✅ Save to Google Sheet (with links)
    save_to_google_sheet([
        str(datetime.now()),
        program_owner,
        training_title,
        venue,
        str(dates),
        qame_other,
        teaching,
        non_teaching,
        teaching_related,
        memo_link,
        matrix_link
    ])

    # ✅ Send email
    send_email_notification(data_dict)

    st.success("✅ MERF submitted, uploaded, recorded, and emailed!")
