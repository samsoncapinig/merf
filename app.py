# 🔹 IMPORTS
import streamlit as st
from datetime import datetime
import gspread
from google.oauth2 import service_account
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# 🔹 GOOGLE SHEETS
def save_to_google_sheet(data):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key("1EZGjn7SX1MhFls_RV4LRt0lhHa1tvOdvK7w2LqUUVLE").sheet1
    sheet.append_row(data)


# 🔹 EMAIL FUNCTION (WITH ATTACHMENTS ✅)
def send_email_notification(data, memo_file=None, matrix_file=None):
    sender = st.secrets["EMAIL_USER"]
    password = st.secrets["EMAIL_PASS"]
    recipients = st.secrets["EMAIL_TO"].split(",")

    msg = MIMEMultipart()
    msg['Subject'] = "MERF Submission"
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

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
"""
    msg.attach(MIMEText(body, "plain"))

    # ✅ Attach Memo File
    if memo_file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(memo_file.getvalue())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{memo_file.name}"'
        )
        msg.attach(part)

    # ✅ Attach Matrix File
    if matrix_file:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(matrix_file.getvalue())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{matrix_file.name}"'
        )
        msg.attach(part)

    # ✅ Send Email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.send_message(msg)


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

    # ✅ Just store file names (no upload anymore)
    memo_name = memo_file.name if memo_file else "No file"
    matrix_name = matrix_file.name if matrix_file else "No file"

    formatted_dates = ", ".join(
        [d.strftime("%Y-%m-%d") for d in dates]
    ) if isinstance(dates, list) else str(dates)

    data_dict = {
        "Program Owner": program_owner,
        "Training Title": training_title,
        "Venue": venue,
        "Dates": formatted_dates,
        "QAME": qame_other,
        "Teaching": teaching,
        "Non-Teaching": non_teaching,
        "Teaching Related": teaching_related,
        "Memo File": memo_name,
        "Matrix File": matrix_name
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
        memo_name,
        matrix_name
    ])

    # ✅ Send email WITH attachments
    send_email_notification(data_dict, memo_file, matrix_file)

    st.success("✅ MERF submitted successfully!")
