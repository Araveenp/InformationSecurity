import streamlit as st
import os
import secrets
from datetime import datetime, timedelta
import json

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

FILES_JSON = "files.json"
def load_files():
    if os.path.exists(FILES_JSON):
        with open(FILES_JSON, "r") as f:
            data = json.load(f)
            # Convert expire_time back to datetime
            for k, v in data.items():
                v["expire_time"] = datetime.fromisoformat(v["expire_time"])
            return data
    return {}

def save_files(files):
    out = {}
    for k, v in files.items():
        v_copy = v.copy()
        v_copy["expire_time"] = v_copy["expire_time"].isoformat()
        out[k] = v_copy
    with open(FILES_JSON, "w") as f:
        json.dump(out, f)

files = load_files()

st.title("Secure File Sharing with Temporary Access Keys")

page = st.sidebar.radio("Select Page", ["Upload", "Download"])

if page == "Upload":
    st.header("Upload File")
    uploaded_file = st.file_uploader("Choose a file", type=["png", "jpg", "jpeg", "pdf", "txt"])
    expire_minutes = st.number_input("Expires in (minutes)", min_value=1, max_value=120, value=10)
    if st.button("Upload") and uploaded_file:
        filename = secrets.token_hex(8) + "_" + uploaded_file.name
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.read())
        key = secrets.token_urlsafe(8)
        expire_time = datetime.utcnow() + timedelta(minutes=expire_minutes)
        files[key] = {
            "filename": uploaded_file.name,
            "filepath": filepath,
            "expire_time": expire_time,
            "download_count": 0,
            "max_downloads": 1
        }
        save_files(files)
        st.success(f"File uploaded! Access Key: {key}")
        st.info(f"Expires at: {expire_time} UTC")
        st.code(f"Use this key on the Download page.")

elif page == "Download":
    st.header("Download File")
    key = st.text_input("Enter Access Key")
    if st.button("Download"):
        file_info = files.get(key)
        if not file_info:
            st.error("Invalid key.")
        elif datetime.utcnow() > file_info["expire_time"]:
            st.error("Key expired.")
        elif file_info["download_count"] >= file_info["max_downloads"]:
            st.error("Download limit reached.")
        else:
            file_info["download_count"] += 1
            save_files(files)
            with open(file_info["filepath"], "rb") as f:
                st.download_button(
                    label=f"Download {file_info['filename']}",
                    data=f.read(),
                    file_name=file_info["filename"]
                )
