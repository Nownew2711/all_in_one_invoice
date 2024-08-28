import os
import glob
import tempfile
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from fpdf import FPDF

def process_pdf(pdf_path, temp_dir):
    pages = convert_from_path(pdf_path)
    selected_images = []
    for i, page in enumerate(pages):
        image_path = os.path.join(temp_dir, f'{os.path.basename(pdf_path)}_{i}.jpg')
        page.save(image_path, 'JPEG')
        text = pytesseract.image_to_string(Image.open(image_path))
        if text.strip().lower().startswith('invoice'):
            selected_images.append(image_path)
    return selected_images

def create_pdf(images, output_path):
    pdf = FPDF()
    for image in images:
        pdf.add_page()
        pdf.image(image, 0, 0, 210, 297)  # A4 size
    pdf.output(output_path, "F")

# Create a temporary directory
with tempfile.TemporaryDirectory() as temp_dir:
    pdf_files = glob.glob('/pdfs/*.pdf')
    all_selected_images = []

    for pdf_file in pdf_files:
        print(f"Processing {pdf_file}...")
        selected_images = process_pdf(pdf_file, temp_dir)
        all_selected_images.extend(selected_images)

    output_path = "/pdfs/output_invoices.pdf"
    create_pdf(all_selected_images, output_path)
    print(f"Created {output_path} with {len(all_selected_images)} invoice images.")

# Temporary directory and its contents are automatically cleaned up when we exit the 'with' block