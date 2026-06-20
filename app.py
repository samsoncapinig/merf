# 🔹 1. IMPORTS
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
from google_auth_oauthlib.flow import Flow
import os

# 🔹 2. GOOGLE SERVICES

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
    sheet = client.open_by_key("1EZGjn7SX1MhFls_RV4LRt0lhHa1tvOdvK7w2LqUUVLE").sheet1
    sheet.append_row(data)

def create_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets["REDIRECT_URI"]],
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ],
        redirect_uri=st.secrets["REDIRECT_URI"],
    )

def upload_to_drive(file, filename):
    creds = st.session_state.get("credentials")

    if not creds:
        st.error("❌ Please login first")
        return ""

    service = build('drive', 'v3', credentials=creds)

    file_stream = io.BytesIO(file.getbuffer())

    media = MediaIoBaseUpload(file_stream, mimetype=file.type)

    file_metadata = {
        'name': filename
        # optional folder:
        # 'parents': ['YOUR_FOLDER_ID']
    }

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded.get('id')

    return f"https://drive.google.com/file/d/{file_id}/view"

def send_email_notification(data):
    sender = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]
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

# 🔹 3. UI FORM (VERY IMPORTANT PART)

st.title("MERF - Monitoring and Evaluation Request Form")

program_owner = st.text_input("Program Owner")
training_title = st.text_input("Training Title")
venue = st.text_input("Venue")
dates = st.date_input("Inclusive Dates", [])

qame_list = [
    "Rose Ann B. Oliva",
    "John Vergel B. Catalina",
    "Amrone Abegaile Mae B. Borromeo",
    "Zaida C. Mendoza",
    "Glady Judd D. Perez",
    "Genelyn Cristobal",
    "John Berben A. Alcala",
    "Mary Ann C. Andales",
    "Arjie A. Señano",
    "Vergil Angelo B. Catalina",
    "Others"
]

qame_selected = st.selectbox("Internal QAME Associate Assigned", qame_list)

if qame_selected == "Others":
    qame_other = st.text_input("Specify Name")
else:
    qame_other = qame_selected

memo_file = st.file_uploader("Upload Signed Memorandum", type=["pdf", "docx"])
matrix_file = st.file_uploader("Upload Activity Matrix", type=["pdf", "docx", "xlsx"])

st.subheader("Number of Participants")
teaching = st.number_input("Teaching", min_value=0)
non_teaching = st.number_input("Non-Teaching", min_value=0)
teaching_related = st.number_input("Teaching Related", min_value=0)

def create_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets["REDIRECT_URI"]],
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/drive"
        ],
        redirect_uri=st.secrets["REDIRECT_URI"],
    )

# 🔹 4. LOG IN BUTTON
flow = create_flow()

auth_url, state = flow.authorization_url(prompt="consent")

st.link_button("🔐 Login with Google", auth_url)

query_params = st.experimental_get_query_params()

if "code" in query_params:
    code = query_params["code"][0]
    flow.fetch_token(code=code)

    credentials = flow.credentials
    st.session_state["credentials"] = credentials

    st.success("✅ Logged in successfully!")

    # ✅ Clear URL params (prevents repeated login)
    st.experimental_set_query_params()

st.subheader("🔐 Google Login Required for File Upload")

flow = create_flow()
auth_url, _ = flow.authorization_url(prompt="consent")

st.link_button("Login with Google", auth_url)

query_params = st.experimental_get_query_params()

if "code" in query_params:
    code = query_params["code"][0]
    flow.fetch_token(code=code)

    st.session_state["credentials"] = flow.credentials
    st.success("✅ Logged in successfully!")

    st.experimental_set_query_params()


# 🔹 4. SUBMIT BUTTON (NOW CORRECT POSITION)

if st.button("Submit MERF"):

    if "credentials" not in st.session_state:
        st.error("❌ Please login with Google first")
        st.stop()

    memo_link = ""
    matrix_link = ""

    if memo_file is not None:
        memo_link = upload_to_drive(memo_file, memo_file.name)

    if matrix_file is not None:
        matrix_link = upload_to_drive(matrix_file, matrix_file.name)

    formatted_dates = ", ".join([d.strftime("%Y-%m-%d") for d in dates]) if isinstance(dates, list) else str(dates)

    data_dict = {
        "Program Owner": program_owner,
        "Training Title": training_title,
        "Venue": venue,
        "Dates": formatted_dates,
        "QAME": qame_other,
        "Teaching": teaching,
        "Non-Teaching": non_teaching,
        "Teaching Related": teaching_related,
        "Memo Link": memo_link,
        "Matrix Link": matrix_link
    }

    save_to_google_sheet([
        str(datetime.now()),
        program_owner,
        training_title,
        venue,
        formatted_dates,
        qame_other,
        teaching,
        non_teaching,
        teaching_related,
        memo_link,
        matrix_link
    ])

    send_email_notification(data_dict)

    st.success("✅ MERF submitted and files uploaded!")
