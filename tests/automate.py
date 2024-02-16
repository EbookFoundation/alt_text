# automate.py - tests the generation of images and benchmarks the systems
# run getbooks.py then downloadbooks.py with input (.txt file), use output for next steps

# imports
import os
import time
import csv
import bs4
from bs4 import BeautifulSoup
from ..src.alttext.alttext import AltTextHTML
from ..src.alttext.langengine import PrivateGPT

# access downloaded books and go thru all of them
# 1. parse html file to find img src to get the before and after context (using get context funct)
# 2. generate alt text using genAltTextV2 (add benchmarking at some point)
# 3. save alt text and benchmarking in a csv (see csv file headings)

# iterate thru downloaded_books folder, pass html into parseFile

class AltTextGenerator(AltTextHTML):
    # uses the class from alttext.py
    # adds relevant benchmarking and saving methods

    def __init__(self):
        super().__init__()
        self.benchmark_records = []

    #Use genAltTextV2
    #ADD benchmark time stamps
    def genAltTextV2(self, src: str) -> str:
        # Start total timing
        total_start_time = time.time()

        # Image data extraction timing
        imgdata_start_time = time.time()
        imgdata = self.getImgData(src)
        imgdata_end_time = time.time()
        imgdata_total_time = imgdata_end_time - imgdata_start_time

        # Context extraction timing
        context = [None, None]
        context_start_time = time.time()
        if self.options["withContext"]:
            context = self.getContext(self.getImg(src))
        context_end_time = time.time()
        context_total_time = context_end_time - context_start_time
        beforeContext = context[0]
        afterContext = context[1]

        # Description generation timing
        genDesc_start_time = time.time()
        desc = self.genDesc(imgdata, src, context)
        genDesc_end_time = time.time()
        genDesc_total_time = genDesc_end_time - genDesc_start_time

        # OCR processing timing
        ocr_start_time = time.time()
        chars = ""
        if self.ocrEngine is not None:
            chars = self.genChars(imgdata, src).strip()
        ocr_end_time = time.time()
        ocr_total_time = ocr_end_time - ocr_start_time

        # Refinement processing timing
        refine_start_time = time.time()
        if self.langEngine is None:
            raise Exception("To use version 2, you must have a langEngine set.")
        refined_desc = self.langEngine.refineAlt(desc, chars, context, None)
        refine_end_time = time.time()
        refine_total_time = refine_end_time - refine_start_time

        # End total timing
        total_end_time = time.time()
        total_overall_time = total_end_time - total_start_time

        #Record dictionary to store all the timing data
        record = {
            "Image Data Extraction Time": imgdata_total_time,
            "Context Extraction Time": context_total_time,
            "Description Generation Time": genDesc_total_time,
            "OCR Processing Time": ocr_total_time,
            "Refinement Processing Time": refine_total_time,
            "Total Overall Time": total_overall_time
        }
        # Add record to benchmark_records for later CSV generation
        self.benchmark_records.append(record)

        return refined_desc

    #CSV generation
    def generate_csv(self, csv_file_path, benchmark_records):
        if not benchmark_records:
            benchmark_records = self.benchmark_records

            if not benchmark_records:
                print("No benchmark data available.")
                return

        # Determine the CSV field names from the keys of the first record
        fieldnames = benchmark_records[0].keys()

        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in benchmark_records:
                writer.writerow(record)
        print(f"CSV file has been generated at: {csv_file_path}")

def automate_process(extr_folder : str):
    # Iterate through all images in a folder to produce a table (csv) with benchmarking

    generator = AltTextGenerator()

    # Iterate thru each book in folder (ex. downloaded_books)
    for book_id in os.listdir(extr_folder):
        book_path = os.path.join(extr_folder, book_id)
        if os.path.isdir(book_path):

            # Iterate thru files in the book's directory
            for filename in os.listdir(book_path):
                filepath = os.path.join(book_path, filename)

                # Check if the file is an HTML file
                if filepath.endswith(".html"):

                    # Use the parseFile method to parse the HTML file for the genAltText function
                    soup = generator.parseFile(filepath)
                    generator.genAltText(soup)

    generator.generate_csv('test_benchmark.csv', generator.benchmark_records)

if __name__ == "__main__":
    print("Running automate.py")

    automate_process('downloaded_books')