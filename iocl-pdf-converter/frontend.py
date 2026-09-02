"""
IOCL PDF-to-Word Converter Project
-----------------------------------
FRONTEND (Streamlit)

This is the webpage a real user will actually see and interact with.
It does NOT do any OCR or conversion itself - it just talks to your
FastAPI backend (app.py) that you already built and tested.

How to run this file:
    1. First, make sure your FastAPI backend is running in one terminal:
           uvicorn app:app --reload
    2. Then, in a SECOND terminal, start this:
           streamlit run frontend.py
    3. It opens automatically at: http://localhost:8501
"""

import base64
import os
import time

import streamlit as st
import requests

from auth import verify_login  # our new login-checking function

BACKEND_URL = "http://127.0.0.1:8000/convert"


# ----------------------------------------------------------------------
# PAGE SETUP
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="PDF to Word Converter",
    page_icon="📄",
    layout="wide",
)

# ----------------------------------------------------------------------
# LOGIN GATE
# This runs BEFORE anything else on the page. If the user hasn't logged
# in yet, we show ONLY the login form and stop the script right there
# using st.stop() - so none of the upload/convert code below even runs
# until login succeeds.
# ----------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_full_name = None

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center; margin-top:60px;'>🔒 Indian Oil Corporation Limited</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888;'>PDF to Word Converter - Please log in</p>", unsafe_allow_html=True)

    login_col1, login_col2, login_col3 = st.columns([1, 1, 1])
    with login_col2:
        with st.container(border=True):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")

            if st.button("Log In", use_container_width=True):
                user_info = verify_login(username_input, password_input)
                if user_info is not None:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user_info["role"]
                    st.session_state.user_full_name = user_info["full_name"]
                    st.rerun()  # reload the page now that login succeeded
                else:
                    st.error("Incorrect username or password.")

    st.stop()  # STOP HERE - don't run any of the code below until logged in


# ----------------------------------------------------------------------
# LOGGED-IN USERS ONLY - everything below this point only runs after
# a successful login, because of the st.stop() above.
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# IOC COLOR THEME (Orange, Navy Blue, White)
# ----------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #f7f8fa;
    }
    .ioc-header {
        background: linear-gradient(135deg, #003876 0%, #00509e 100%);
        padding: 32px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 28px;
        box-shadow: 0 4px 14px rgba(0, 56, 118, 0.25);
    }
    .main .block-container {
        max-width: 900px;
        margin: 0 auto;
        padding-top: 2rem;
    }
    .ioc-header img {
        height: 90px;
        margin-bottom: 14px;
    }
    .ioc-header h1 {
        color: #ffffff;
        font-size: 30px;
        margin: 6px 0 0 0;  
        font-weight: 700;
    }
    .ioc-header p {
        color: #f2a900;
        font-size: 15px;
        margin-top: 8px;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-left: 5px solid #f2a900 !important;
        border-radius: 12px !important;
        padding: 6px;
        background-color: #ffffff;
    }
    .stButton>button {
        background-color: #f2a900;
        color: #003876;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        padding: 10px 28px;
    }
    .stButton>button:hover {
        background-color: #d99400;
        color: #ffffff;
    }
    .stDownloadButton>button {
        background-color: #003876;
        color: #ffffff;
        font-weight: bold;
        border-radius: 6px;
        border: none;
        padding: 10px 28px;
    }
    .stDownloadButton>button:hover {
        background-color: #f2a900;
        color: #003876;
    }
    .ioc-footer {
        text-align: center;
        color: #8a8a8a;
        font-size: 13px;
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)


def get_logo_html_tag():
    """
    If ioc_logo.png exists in the project folder, convert it to a format
    that can be embedded directly inside our HTML header (base64 text).
    Returns an empty string if no logo file is found - the header still
    works fine without one.
    """
    if not os.path.exists("ioc_logo.png"):
        return ""
    with open("ioc_logo.png", "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f'<img src="data:image/png;base64,{encoded}">'


# ----------------------------------------------------------------------
# HEADER SECTION
# IMPORTANT FIX: everything (logo + title + subtitle) is built as ONE
# single HTML string and shown with ONE st.markdown() call. Splitting a
# <div> across multiple st.markdown() calls is what caused the empty
# white/blue bars you saw before - newer Streamlit versions render each
# st.markdown() call as its own separate block, so it can't "wrap"
# content that comes from a different call.
# ----------------------------------------------------------------------
logo_tag = get_logo_html_tag()

# ----------------------------------------------------------------------
# SIDEBAR
# A sidebar makes the page feel like a complete application rather than
# a single narrow form, and gives space for instructions/branding
# without cluttering the main upload area.
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user_full_name}")
    st.markdown(f"Role: **{st.session_state.user_role.capitalize()}**")
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_full_name = None
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    1. Upload a PDF document
    2. Click **Convert to Word**
    3. Wait while the system extracts text, tables, and structure
    4. Download your editable Word file
    """)
    st.markdown("---")
    st.markdown("### 🖥️ Engine")
    st.markdown("**Docling** (CPU-based OCR)")
    st.markdown("Preserves headings, paragraphs, and tables.")
    st.markdown("---")
    st.markdown("### 📌 Notes")
    st.markdown("- Maximum file size: 200 MB\n- Only PDF files are accepted\n- Processing time depends on document length")

    # ------------------------------------------------------------------
    # ADMIN-ONLY SECTION - this is RBAC in action. Only users whose role
    # is "admin" see this part of the sidebar at all. A regular "user"
    # role never sees this section, since the code inside this "if"
    # simply never runs for them.
    # ------------------------------------------------------------------
    if st.session_state.user_role == "admin":
        st.markdown("---")
        st.markdown("### 🛠️ Admin Panel")
        upload_count = len(os.listdir("uploads")) if os.path.exists("uploads") else 0
        output_count = len(os.listdir("outputs")) if os.path.exists("outputs") else 0
        st.markdown(f"Total uploads: **{upload_count}**")
        st.markdown(f"Total conversions: **{output_count}**")


st.markdown(f"""
    <div class="ioc-header">
        {logo_tag}
        <h1>Indian Oil Corporation Limited</h1>
        <p>PDF to Word Converter &nbsp;</p>
    </div>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# STATE MANAGEMENT
# ----------------------------------------------------------------------
if "converted_file" not in st.session_state:
    st.session_state.converted_file = None
    st.session_state.converted_filename = None


# ----------------------------------------------------------------------
# STATE 1: UPLOAD
# FIX: using st.container(border=True) - Streamlit's own built-in card
# component - instead of manually written HTML divs. This is the
# correct, version-safe way to get a "card" look around real widgets.
# ----------------------------------------------------------------------
with st.container(border=True):
    st.subheader("📤 Upload a PDF document")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        file_size_kb = round(len(uploaded_file.getvalue()) / 1024, 1)
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown(f"**File name:** {uploaded_file.name}")
        with detail_col2:
            st.markdown(f"**File size:** {file_size_kb} KB")

        if st.button("Convert to Word"):
            # ----------------------------------------------------------
            # STATE 2: PROCESSING - staged progress bar
            #
            # HONEST NOTE ON HOW THIS WORKS: our FastAPI backend currently
            # does the whole conversion in one go and only replies once
            # it's fully finished - it doesn't report "I'm 40% done" back
            # to us in real time (that would need a more advanced setup
            # like websockets). So instead, we run the upload in a
            # background thread and show a progress bar that steps through
            # realistic stage messages while we wait, then jumps to 100%
            # the moment the real response arrives. This gives a much
            # better sense of progress than a plain spinner, without
            # pretending to know an exact byte-by-byte percentage.
            # ----------------------------------------------------------
            import threading

            result_holder = {}

            def send_request():
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    result_holder["response"] = requests.post(BACKEND_URL, files=files)
                except requests.exceptions.ConnectionError:
                    result_holder["error"] = "connection"

            worker_thread = threading.Thread(target=send_request)
            worker_thread.start()

            progress_bar = st.progress(0, text="Uploading document...")
            stages = [
                (15, "Uploading document..."),
                (40, "Extracting text and tables with Docling..."),
                (70, "Detecting headings and structure..."),
                (90, "Building your Word document..."),
            ]
            stage_index = 0

            while worker_thread.is_alive():
                if stage_index < len(stages):
                    pct, msg = stages[stage_index]
                    progress_bar.progress(pct, text=msg)
                    stage_index += 1
                worker_thread.join(timeout=0.8)

            progress_bar.progress(100, text="Finalizing...")
            time.sleep(0.3)
            progress_bar.empty()

            if "error" in result_holder:
                st.error(
                    "Could not reach the backend server. "
                    "Make sure 'uvicorn app:app --reload' is running in another terminal."
                )
            else:
                response = result_holder["response"]
                if response.status_code == 200:
                    st.session_state.converted_file = response.content
                    st.session_state.converted_filename = uploaded_file.name.replace(".pdf", "_converted.docx")
                    st.success("✅ Conversion completed successfully.")
                else:
                    st.error(f"Conversion failed: {response.json().get('detail', 'Unknown error')}")


# ----------------------------------------------------------------------
# STATE 3: DOWNLOAD
# ----------------------------------------------------------------------
if st.session_state.converted_file is not None:
    with st.container(border=True):
        st.subheader("📄 Your Word document is ready")
        st.download_button(
            label="Download Word File",
            data=st.session_state.converted_file,
            file_name=st.session_state.converted_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown("""
    <div class="ioc-footer">
        Internal tool developed by the Information Systems Department &nbsp;|&nbsp; Indian Oil Corporation Limited
    </div>
""", unsafe_allow_html=True)
