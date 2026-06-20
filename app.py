# 🔹 1. IMPORTS (top of file)
import streamlit as st
import pandas as pd
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# 🔹 2. GOOGLE DRIVE FUNCTION (put it HERE ✅)

def get_drive_service():
    SCOPES = ['https://www.googleapis.com/auth/drive']

    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES)

    service = build('drive', 'v3', credentials=creds)
    return service
    
# 🔹 3. UPLOAD FUNCTION (below it ✅)

def upload_to_drive(file, filename):
    service = get_drive_service()

    file_metadata = {
        'name': filename,
        'parents': ['1gHafPfK31w9nQ3siyVW4BpbsCs7VVS_X?fbclid=IwY2xjawRZCWFleHRuA2FlbQMxMDAAc3J0YwZhcHBfaWQBMAABHo7zyITbqfVjzwEnjGp9Z3RTyk8I52rKMWaXp_i7SxcIxDT_FG0DuJSA67M8_aem_HCMy1GEuAYyziXthnGsSCg']
    }

    file_stream = io.BytesIO(file.getbuffer())

    media = MediaIoBaseUpload(file_stream, mimetype=file.type)

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return uploaded.get('id')
    

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

if st.button("Submit MERF"):

    if memo_file:
        upload_to_drive(memo_file, memo_file.name)

    if matrix_file:
        upload_to_drive(matrix_file, matrix_file.name)

    st.success("MERF submitted and uploaded to Google Drive ✅")
