# 🔹 IMPORTS
import streamlit as st
from datetime import datetime
import gspread
from google.oauth2 import service_account
import smtplib
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from googleapiclient.errors import HttpError

# 🔹 GOOGLE SHEETS
def save_to_google_sheet(data):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)

    client = gspread.authorize(creds)
    sheet = client.open_by_key("1EZGjn7SX1MhFls_RV4LRt0lhHa1tvOdvK7w2LqUUVLE").sheet1
    sheet.append_row(data)

# 🔹 GOOGLE DRIVE UPLOAD

def upload_to_gdrive(file, filename):
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']

        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES)

        service = build('drive', 'v3', credentials=creds)

        file_stream = io.BytesIO(file.getvalue())

        media = MediaIoBaseUpload(
            file_stream,
            mimetype=file.type,
            resumable=False   # ✅ IMPORTANT: disable chunking for Streamlit
        )

        file_metadata = {
            'name': f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}",
            'parents': ['11mUXkWqeGRWShnL8vbVqftx9C9rcodl6']
        }

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # ✅ Make file public
        service.permissions().create(
            fileId=uploaded_file['id'],
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()

        return uploaded_file.get("webViewLink")

    except HttpError as error:
        st.error(f"❌ Google Drive API error:\n{error}")
        return None

    except Exception as e:
        st.error(f"❌ Unexpected error:\n{str(e)}")
        return None
    
# 🔹 EMAIL FUNCTION
def send_email_notification(data):
    sender = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]
    recipients = st.secrets["EMAIL_TO"].split(",")

    body = f"""
New MERF Submission:

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
Memo: {data['Memo File']}
Matrix: {data['Matrix File']}
"""

    msg = MIMEText(body)
    msg['Subject'] = "MERF Submission"
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)

import requests
import msal

def get_access_token():
    authority = f"https://login.microsoftonline.com/{st.secrets['MS_TENANT_ID']}"
    
    app = msal.ConfidentialClientApplication(
        st.secrets["MS_CLIENT_ID"],
        authority=authority,
        client_credential=st.secrets["MS_CLIENT_SECRET"],
    )

    token = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )

    if "access_token" in token:
        return token["access_token"]
    else:
        st.error(f"❌ Token error: {token}")
        return None


# 🔹 UI FORM
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

# 🔹 SUBMIT
if st.button("Submit MERF"):

    if not program_owner or not training_title:
        st.error("❌ Please fill required fields")
        st.stop()

    memo_link = "No file"
    matrix_link = "No file"

    if memo_file:
        memo_link = upload_to_gdrive(memo_file, memo_file.name)

    if matrix_file:
        matrix_link = upload_to_gdrive(matrix_file, matrix_file.name)

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
        "Memo File": memo_link,
        "Matrix File": matrix_link
    }

    # ✅ Save to sheet
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

    # ✅ Send email
    send_email_notification(data_dict)

    st.success("✅ MERF submitted successfully!")
