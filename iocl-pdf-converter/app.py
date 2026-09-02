"""
IOCL PDF-to-Word Converter Project
-----------------------------------
FASTAPI BACKEND

This file turns your working docling_to_word.py logic into a real web
service. It doesn't change any of your conversion logic - it just adds
a "front door" so a browser can upload a PDF and get a Word file back.

Install requirements (if not already done):
    pip install fastapi uvicorn python-multipart

How to run this file:
    uvicorn app:app --reload

Then open this in your browser to test it (FastAPI gives you a free
built-in testing page):
    http://127.0.0.1:8000/docs
"""

import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

# This imports the function you already wrote and tested
from docling_to_word import convert_pdf_to_word

# Create the FastAPI application - this is your actual "web app" object
app = FastAPI(title="IOCL PDF to Word Converter")

# Folders where uploaded PDFs and generated Word files will be stored.
# We create them automatically if they don't already exist.
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.get("/")
def home():
    """
    A simple check to confirm the server is running.
    Visiting http://127.0.0.1:8000/ in a browser will show this message.
    """
    return {"message": "IOCL PDF to Word Converter is running."}


@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    """
    THE MAIN ENDPOINT.

    This function runs whenever someone uploads a PDF through the
    "/convert" address. Here's what happens step by step:

      1. Check the uploaded file is actually a PDF.
      2. Save it into the uploads/ folder with a unique name (so two
         different users uploading "report.pdf" at the same time don't
         overwrite each other).
      3. Call your existing convert_pdf_to_word() function - the exact
         same one you already tested from the terminal.
      4. Send the finished Word file back to the browser as a download.
    """

    # Step 1: basic validation - reject anything that isn't a PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    # Step 2: create a unique filename so uploads never clash with each other
    unique_id = uuid.uuid4().hex
    input_pdf_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")
    output_docx_path = os.path.join(OUTPUT_FOLDER, f"{unique_id}.docx")

    # Save the uploaded PDF to disk
    with open(input_pdf_path, "wb") as saved_file:
        content = await file.read()
        saved_file.write(content)

    # Step 3: run your existing, already-tested conversion function
    try:
        convert_pdf_to_word(input_pdf_path, output_docx_path)
    except Exception as conversion_error:
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {conversion_error}"
        )

    # Step 4: send the finished Word file back to the browser as a download.
    # FileResponse handles reading the file and setting the correct headers
    # so the browser knows to offer it as a downloadable .docx file.
    original_name_without_extension = os.path.splitext(file.filename)[0]
    download_filename = f"{original_name_without_extension}_converted.docx"

    return FileResponse(
        path=output_docx_path,
        filename=download_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )