"""
IOCL PDF-to-Word Converter Project
-----------------------------------
This script compares the three CPU OCR engines (Tesseract, PaddleOCR, Docling)
by running the same sample PDF through each one and printing:
  - the extracted text
  - the time each engine took

This is the evidence you'll use in your documentation to justify which
engine you chose as the main CPU OCR engine for the project.
"""

import time

PDF_PATH = "sample_test_document.pdf"   # change this if your file has a different name


def run_tesseract(pdf_path):
    """Runs Tesseract OCR on every page of the PDF and returns the combined text."""
    import pytesseract
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_path)
    extracted_text = ""

    for page_number in range(len(pdf)):
        page = pdf[page_number]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()
        extracted_text += pytesseract.image_to_string(pil_image)

    return extracted_text.strip()


def run_paddleocr(pdf_path):
    """Runs PaddleOCR on every page of the PDF and returns the combined text."""
    from paddleocr import PaddleOCR
    import pypdfium2 as pdfium
    import numpy as np

    ocr_engine = PaddleOCR(lang="en", enable_mkldnn=False, use_textline_orientation=True)
    pdf = pdfium.PdfDocument(pdf_path)
    extracted_text = ""

    for page_number in range(len(pdf)):
        page = pdf[page_number]
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil().convert("RGB")
        image_array = np.array(pil_image)

        results = ocr_engine.predict(image_array)
        for res in results:
            text_lines = res["rec_texts"]
            extracted_text += "\n".join(text_lines) + "\n"

    return extracted_text.strip()


def run_docling(pdf_path):
    """Runs Docling on the PDF and returns the extracted content as markdown."""
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown().strip()


def run_engine_safely(engine_name, engine_function, pdf_path):
    """Wraps each engine call so one engine failing doesn't stop the others."""
    print(f"\n{'=' * 60}")
    print(f"Running {engine_name} ...")
    print("=" * 60)

    start_time = time.time()
    try:
        extracted_text = engine_function(pdf_path)
        elapsed = time.time() - start_time
        print(f"[{engine_name}] Completed in {elapsed:.2f} seconds")
        print(f"[{engine_name}] Extracted text:\n")
        print(extracted_text)
        return {"engine": engine_name, "time_seconds": elapsed, "text": extracted_text, "status": "success"}
    except Exception as error:
        elapsed = time.time() - start_time
        print(f"[{engine_name}] FAILED after {elapsed:.2f} seconds")
        print(f"[{engine_name}] Error: {error}")
        return {"engine": engine_name, "time_seconds": elapsed, "text": "", "status": "failed"}


if __name__ == "__main__":
    results = []
    results.append(run_engine_safely("Tesseract", run_tesseract, PDF_PATH))
    results.append(run_engine_safely("PaddleOCR", run_paddleocr, PDF_PATH))
    results.append(run_engine_safely("Docling", run_docling, PDF_PATH))

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Engine':<15}{'Status':<12}{'Time (seconds)':<15}{'Characters extracted'}")
    for r in results:
        print(f"{r['engine']:<15}{r['status']:<12}{r['time_seconds']:<15.2f}{len(r['text'])}")