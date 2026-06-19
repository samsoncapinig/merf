
import streamlit as st
import pandas as pd
from datetime import datetime
import os

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

    # ✅ Your OneDrive folder path here
    upload_path = "/Users/macbookair/Library/CloudStorage/OneDrive-DEPARTMENTOFEDUCATION/MERF\ Uploads"
    os.makedirs(upload_path, exist_ok=True)

    memo_path = ""
    matrix_path = ""

    # Save Signed Memorandum
    if memo_file:
        memo_path = os.path.join(upload_path, memo_file.name)
        with open(memo_path, "wb") as f:
            f.write(memo_file.getbuffer())

    # Save Activity Matrix
    if matrix_file:
        matrix_path = os.path.join(upload_path, matrix_file.name)
        with open(matrix_path, "wb") as f:
            f.write(matrix_file.getbuffer())
        with open(memo_path, "wb") as f:
            f.write(memo_file.getbuffer())

    if matrix_file:
        matrix_path = f"uploads/{matrix_file.name}"
        with open(matrix_path, "wb") as f:
            f.write(matrix_file.getbuffer())

    data = {
        "Program Owner": program_owner,
        "Training Title": training_title,
        "Venue": venue,
        "Dates": str(dates),
        "QAME": qame_other,
        "Memo File": memo_path,
        "Activity Matrix": matrix_path,
        "Teaching": teaching,
        "Non-Teaching": non_teaching,
        "Teaching Related": teaching_related,
        "Timestamp": datetime.now()
    }

    df = pd.DataFrame([data])

    if os.path.exists("merf_data.csv"):
        df.to_csv("merf_data.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("merf_data.csv", index=False)

    st.success("MERF submitted successfully!")
