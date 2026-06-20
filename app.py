# 🔹 1. IMPORTS
import streamlit as st
from datetime import datetime
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import Flow
import io
import smtplib
from email.mime.text import MIMEText
import os

# ✅ Fix for OAuth redirect
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# 🔹 2. GOOGLE SHEETS
def save_to_google_sheet(data):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)

    client = gspread.authorize(creds)
    sheet = client.open_by_key("1EZGjn7SX1MhFls_RV4LRt0lhHa1tvOdvK7w2LqUUVLE").sheet1
    sheet.append_row(data)

# 🔹 3. EMAIL FUNCTION
def send_email_notification(data):
    sender = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]
    recipients = st.secrets["EMAIL_TO"].split(",")

    msg = MIMEText(f"""
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
Memo: {data['Memo Link']}
Matrix: {data['Matrix Link']}
""")

    msg['Subject'] = "MERF Submission"
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)

# 🔹 4. OAUTH FLOW
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
        scopes=["https://www.googleapis.com/auth/drive"],
        redirect_uri=st.secrets["REDIRECT_URI"],
    )

# 🔹 5. UPLOAD FUNCTION
def upload_to_drive(file, filename):
    creds = st.session_state.get("credentials")

    if not creds:
        st.error("❌ Login first")
        return ""

    service = build('drive', 'v3', credentials=creds)

    file_stream = io.BytesIO(file.getbuffer())

    media = MediaIoBaseUpload(file_stream, mimetype=file.type)

    uploaded = service.files().create(
        body={"name": filename},
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded.get('id')

    return f"https://drive.google.com/file/d/{file_id}/view"

# 🔹 6. UI
st.title("MERF Form")

program_owner = st.text_input("Program Owner")
training_title = st.text_input("Training Title")
venue = st.text_input("Venue")
dates = st.date_input("Dates", [])

qame = st.text_input("QAME")

memo_file = st.file_uploader("Signed Memorandum")
matrix_file = st.file_uploader("Activity Matrix")

teaching = st.number_input("Teaching", 0)
non_teaching = st.number_input("Non-Teaching", 0)
related = st.number_input("Teaching Related", 0)

# 🔹 7. LOGIN
st.subheader("🔐 Login with Google")

flow = create_flow()
auth_url, _ = flow.authorization_url(prompt="consent")

st.link_button("Login", auth_url)

params = st.query_params

if "code" in params:
    code = params["code"]
    flow.fetch_token(code=code)

    st.session_state["credentials"] = flow.credentials
    st.success("✅ Logged in")

    # ✅ Clear params (new way)
    st.query_params.clear()


# 🔹 8. SUBMIT
if st.button("Submit"):

    if "credentials" not in st.session_state:
        st.error("Login first")
        st.stop()

    memo_link = upload_to_drive(memo_file, memo_file.name) if memo_file else ""
    matrix_link = upload_to_drive(matrix_file, matrix_file.name) if matrix_file else ""

    date_str = ", ".join([d.strftime("%Y-%m-%d") for d in dates])

    data = {
        "Program Owner": program_owner,
        "Training Title": training_title,
        "Venue": venue,
        "Dates": date_str,
        "QAME": qame,
        "Teaching": teaching,
        "Non-Teaching": non_teaching,
        "Teaching Related": related,
        "Memo Link": memo_link,
        "Matrix Link": matrix_link
    }

    save_to_google_sheet([
        str(datetime.now()), program_owner, training_title, venue,
        date_str, qame, teaching, non_teaching, related,
        memo_link, matrix_link
    ])

    send_email_notification(data)

    st.success("✅ Submitted with file upload!")
