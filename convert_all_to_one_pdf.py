import os
import glob
import re
import tempfile
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from fpdf import FPDF
import cv2
import numpy as np
from fuzzywuzzy import fuzz  # Importing fuzzywuzzy for fuzzy matching

def correct_orientation(image):
    # Convert to RGB if grayscale
    if len(image.shape) == 2 or image.shape[2] == 1:  # Grayscale image
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # Detect text orientation using Tesseract's OSD feature
    osd = pytesseract.image_to_osd(image)
    rotation_angle = int(re.search(r'Rotate: (\d+)', osd).group(1))
    
    # Rotate the image based on the detected angle
    if rotation_angle == 90:
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_angle == 180:
        image = cv2.rotate(image, cv2.ROTATE_180)
    elif rotation_angle == 270:
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    
    return image
    
def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Apply thresholding to binarize the image
    _, image = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)
    # Use dilation and erosion to remove noise
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    image = cv2.erode(image, kernel, iterations=1)
    return image

# Function to check if the page contains "INVOICE" using fuzzy matching
def is_invoice_page(text):
    return fuzz.partial_ratio("INVOICE", text) > 80

# Function to process a PDF and extract pages that start with "INVOICE"
def process_pdf(pdf_path, temp_dir, dpi=150):
    selected_images = []
    
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, dpi=dpi)
    
    for i, page in enumerate(pages):
        image_path = os.path.join(temp_dir, f'{os.path.basename(pdf_path)}_page_{i+1}.jpg')
        page.save(image_path, 'JPEG')
        
        # Preprocess the image
        processed_image = preprocess_image(image_path)
        # Correct the orientation of the image
        corrected_image = correct_orientation(processed_image)

        text1 = pytesseract.image_to_string(corrected_image, config='--psm 6').strip().upper()
        # Second pass with different configuration
        text2 = pytesseract.image_to_string(corrected_image, config='--psm 3').strip().upper()
        # Combine or compare results
        text = text1 + "\n" + text2
        
        # Check if the page is an invoice using fuzzy matching
        if is_invoice_page(text):
            selected_images.append(image_path)
            
        # # Check if the page starts with "INVOICE"
        # if text.startswith("INVOICE"):
        #     selected_images.append(image_path)
        # Check if "INVOICE" is within the first few lines
        # lines = text.splitlines()
        # if any(line.startswith("INVOICE") for line in lines[:5]):  # Check the first 5 lines
        #     selected_images.append(image_path)


    return selected_images

# Function to create a PDF from selected images
def create_pdf(images, output_path):
    pdf = FPDF()
    for image in images:
        pdf.add_page()
        pdf.image(image, 0, 0, 210, 297)  # A4 size in mm
    pdf.output(output_path, "F")

# Main function
def main():
    # Get the current directory (where the script and PDFs are located)
    current_dir = os.getcwd()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_files = glob.glob(os.path.join(current_dir, '*.pdf'))
        all_selected_images = []

        for pdf_file in pdf_files:
            print(f"Processing {pdf_file}...")
            selected_images = process_pdf(pdf_file, temp_dir)
            all_selected_images.extend(selected_images)

        if all_selected_images:
            output_path = os.path.join(current_dir, "output_invoices.pdf")
            create_pdf(all_selected_images, output_path)
            print(f"Created {output_path} with {len(all_selected_images)} selected pages.")
        else:
            print("No pages found that start with 'INVOICE'.")

if __name__ == "__main__":
    main()
