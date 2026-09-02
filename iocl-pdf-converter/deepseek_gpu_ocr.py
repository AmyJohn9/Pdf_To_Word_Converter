import os
# Load Python's built-in tool for working with files and folders
 
import logging
# Load Python's built-in tool for printing status/progress messages
 
import tempfile
# Load Python's built-in tool for creating temporary folders that auto-delete later
 
from pathlib import Path
# Load a tool that makes working with file paths easier and more readable
 
from typing import List
# Load a tool used only for labeling what type of data a function expects/returns
 
import torch
# Load PyTorch, the AI/deep learning engine that runs the GPU model
 
from transformers import AutoModel, AutoTokenizer
# Load Hugging Face's tools for loading pretrained AI models and their tokenizers
 
import pypdfium2 as pdfium
# Load the library used to open PDFs and turn their pages into images
 
from docling_to_word import markdown_to_word
# Import your already-tested function that turns Markdown text into a Word file
 
logger = logging.getLogger(__name__)
# Create a "logger" object so this file can print organized status messages
 
MODEL_NAME = "baidu/Unlimited-OCR"
# Store the exact name/ID of the AI model we're going to load, in one place
 
MULTI_PAGE_IMAGE_SIZE = 1024
# Store the image size (in pixels) the model expects, as defined in its official docs
 
MAX_LENGTH = 32768
# Store the maximum amount of text the model is allowed to generate in one go
 
NO_REPEAT_NGRAM_SIZE = 35
# Store a setting that stops the model from repeating the same phrase over and over
 
NGRAM_WINDOW = 128
# Store another repetition-control setting, as specified in the model's official docs
 
 
def pdf_to_images(pdf_path: str, output_dir: str, scale: float = 2.0) -> List[str]:
# Define a function that turns a PDF into a series of image files
 
    os.makedirs(output_dir, exist_ok=True)
    # Create the output folder if it doesn't already exist
 
    pdf = pdfium.PdfDocument(pdf_path)
    # Open the PDF file so we can read its pages
 
    image_paths = []
    # Create an empty list to collect the file paths of the images we're about to make
 
    for page_number in range(len(pdf)):
    # Loop through every page in the PDF, one at a time
 
        page = pdf[page_number]
        # Get the current page we're working on
 
        bitmap = page.render(scale=scale)
        # Render (draw) this page as an image, at the requested zoom/quality level
 
        pil_image = bitmap.to_pil().convert("RGB")
        # Convert that rendered image into a standard image format (RGB colors)
 
        image_path = os.path.join(output_dir, f"page_{page_number + 1:03d}.png")
        # Build the file name/path this page's image will be saved as (e.g. page_001.png)
 
        pil_image.save(image_path)
        # Actually save the image file to disk
 
        image_paths.append(image_path)
        # Add this image's file path to our running list
 
    return image_paths
    # Give back the full list of image file paths, one per page, in order
 
 
class UnlimitedOCREngine:
# Define a class (a reusable "tool") that wraps the Unlimited-OCR model
 
    def __init__(self, device: str = "cuda"):
    # Define what happens when this tool is first created/set up
 
        if not torch.cuda.is_available():
        # Check: does this computer actually have a usable NVIDIA GPU?
 
            raise RuntimeError(
                "UnlimitedOCREngine requires an NVIDIA GPU. "
                "torch.cuda.is_available() returned False. "
                "This code path must be run on a GPU-enabled machine."
            )
            # If no GPU is found, stop immediately with a clear error message
 
        logger.info("Loading %s ...", MODEL_NAME)
        # Print a message saying the model is starting to load
 
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, trust_remote_code=True
        )
        # Download/load the model's "tokenizer" - the part that prepares text for the model
 
        self.model = AutoModel.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=torch.bfloat16,
        )
        # Download/load the actual AI model itself, using a memory-efficient number format
 
        self.model = self.model.eval().to(device)
        # Switch the model into "reading mode" (not training mode) and move it onto the GPU
 
        logger.info("Unlimited-OCR model loaded on %s", device)
        # Print a message confirming the model finished loading successfully
 
    def run_multi_page(self, image_files: List[str], output_dir: str) -> str:
    # Define a function that feeds multiple page-images into the model at once
 
        os.makedirs(output_dir, exist_ok=True)
        # Create the folder where the model's results will be saved, if needed
 
        self.model.infer_multi(
            self.tokenizer,
            prompt="<image>Multi page parsing.",
            image_files=image_files,
            output_path=output_dir,
            image_size=MULTI_PAGE_IMAGE_SIZE,
            max_length=MAX_LENGTH,
            save_results=True,
        )
        # Actually run the AI model on all the page images, telling it to read/parse them
 
        return _read_markdown_output(output_dir)
        # Collect and return the text results the model just saved to disk
 
 
def _read_markdown_output(output_dir: str) -> str:
# Define a helper function that gathers the model's saved text output
 
    md_extensions = (".md", ".mmd", ".markdown")
    # List the file types we expect the model's output to be saved as
 
    out_path = Path(output_dir)
    # Turn the output folder location into a easier-to-use path object
 
    md_files = sorted(
        p for p in out_path.iterdir() if p.suffix.lower() in md_extensions
    )
    # Find every file in that folder matching those text file types, sorted in order
 
    if not md_files:
    # If no matching text files were found at all...
 
        raise FileNotFoundError(
            f"No markdown output found in {output_dir}. "
            "Inspect the directory contents on a GPU run and update "
            "_read_markdown_output() to match the real file layout."
        )
        # ...stop and clearly explain that something unexpected happened
 
    chunks = [f.read_text(encoding="utf-8") for f in md_files]
    # Read the actual text content out of every one of those found files
 
    return "\n\n".join(chunks)
    # Join all those pieces of text together into one combined block, and return it
 
 
def gpu_pdf_to_word(pdf_path: str, output_docx_path: str) -> str:
# Define the main "do everything" function for the whole GPU pipeline
 
    with tempfile.TemporaryDirectory() as tmp_dir:
    # Create a temporary folder to work in, which will auto-delete when done
 
        image_paths = pdf_to_images(pdf_path, tmp_dir)
        # Step 1: turn the PDF into a list of page images
 
        engine = UnlimitedOCREngine()
        # Step 2a: load the Unlimited-OCR model, ready to use
 
        ocr_output_dir = os.path.join(tmp_dir, "ocr_out")
        # Decide where the model's raw text output will be temporarily saved
 
        markdown_text = engine.run_multi_page(image_paths, ocr_output_dir)
        # Step 2b: send all the page images to the model and get structured text back
 
        markdown_to_word(markdown_text, output_docx_path)
        # Step 3: convert that structured text into a real Word (.docx) file
 
    return output_docx_path
    # Give back the path to the finished Word file
 
 
if __name__ == "__main__":
# This block only runs if you execute this file directly (not when imported elsewhere)
 
    import argparse
    # Load a tool for reading command-line arguments (like a file name typed after the command)
 
    parser = argparse.ArgumentParser(
        description="Convert a PDF to Word using the Unlimited-OCR GPU engine."
    )
    # Set up a simple command-line interface with a description
 
    parser.add_argument("pdf_path", help="Path to input PDF")
    # Define the first required input: the path to the PDF file to convert
 
    parser.add_argument("output_docx", help="Path to output .docx file")
    # Define the second required input: where to save the resulting Word file
 
    args = parser.parse_args()
    # Actually read whatever the user typed in when running this script
 
    logging.basicConfig(level=logging.INFO)
    # Turn on printing of status messages while this script runs
 
    result_path = gpu_pdf_to_word(args.pdf_path, args.output_docx)
    # Run the entire pipeline using the file paths the user provided
 
    print(f"Word document written to: {result_path}")
    # Print a final confirmation message showing where the output file was saved