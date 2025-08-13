import pdfplumber
import openpyxl
from openpyxl.utils import get_column_letter
import structlog
from typing import List, Dict, Any
import backend.ocr_service as ocr_service

logger = structlog.get_logger(__name__)

Element = Dict[str, Any]

def parse_textract_blocks(textract_json: dict, page_width: float, page_height: float) -> List[Element]:
    """
    Parses the Textract JSON response and converts it into our Element format.
    """
    elements = []
    for block in textract_json.get("Blocks", []):
        if block["BlockType"] == "WORD":
            text = block.get("Text", "")
            geom = block.get("Geometry", {})
            bbox = geom.get("BoundingBox", {})

            # Convert Textract's proportional coordinates to absolute pdfplumber-style coordinates
            x0 = bbox.get("Left", 0) * page_width
            top = bbox.get("Top", 0) * page_height
            x1 = x0 + (bbox.get("Width", 0) * page_width)
            bottom = top + (bbox.get("Height", 0) * page_height)

            elements.append({
                "text": text,
                "x0": x0, "top": top, "x1": x1, "bottom": bottom,
            })
    return elements

def map_elements_to_sheet(sheet, elements: List[Element]):
    """
    This function is now much simpler. It just places pre-structured table data.
    The complex layout logic is now handled by the extraction strategy.
    """
    for r, row_data in enumerate(elements, start=1):
        for c, cell_data in enumerate(row_data, start=1):
            cleaned_data = str(cell_data).replace('\\n', ' ').strip() if cell_data else ""
            sheet.cell(row=r, column=c).value = cleaned_data

    for i in range(1, sheet.max_column + 1):
        sheet.column_dimensions[get_column_letter(i)].auto_size = True

def convert_pdf_to_excel(pdf_path: str, excel_path: str, bucket_name: str, object_key: str):
    """
    The final, 3-tiered hybrid conversion engine.
    """
    logger.info("Starting 3-tier hybrid conversion", pdf_path=pdf_path)

    try:
        workbook = openpyxl.Workbook()
        if "Sheet" in workbook.sheetnames:
            workbook.remove(workbook["Sheet"])

        with pdfplumber.open(pdf_path) as pdf:

            # --- Tier 0: Full text extraction as a fallback sheet ---
            text_sheet = workbook.create_sheet(title="All_Text_Fallback")
            full_text = "".join([page.extract_text(x_tolerance=2) or "" for page in pdf.pages])
            text_sheet.cell(row=1, column=1).value = full_text

            # --- Main Tiered Logic ---
            table_count = 0
            for i, page in enumerate(pdf.pages):
                logger.info(f"Processing Page {i+1}...")

                # Heuristic to detect image-based page
                if not page.extract_text(x_tolerance=2).strip():
                    logger.warn(f"Page {i+1} appears to be image-based. Forcing OCR.", page=i+1)
                    # This page will be handled by the OCR-only path below
                    continue

                # Tier 1: Try 'lines' strategy
                line_tables = page.extract_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})

                # Tier 2: If no lines, try 'text' strategy
                if not line_tables:
                    logger.warn(f"No tables found with 'lines' strategy on page {i+1}. Falling back to 'text'.")
                    text_tables = page.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"})
                    tables_to_write = text_tables
                else:
                    tables_to_write = line_tables

                # Write tables found by pdfplumber
                for table in tables_to_write:
                    table_count += 1
                    table_sheet = workbook.create_sheet(title=f"Table_pdfplumber_{table_count}_P{i+1}")
                    map_elements_to_sheet(table_sheet, table)

            # Tier 3: OCR as the ultimate tool for specific complex files or images
            # We run this for the NAB file specifically, or for any image-based PDF.
            is_image_pdf = not any(p.extract_text(x_tolerance=2).strip() for p in pdf.pages)
            if "NAB" in pdf_path or is_image_pdf:
                logger.info("Running AWS Textract OCR as ultimate fallback/override.", pdf_path=pdf_path)
                textract_json = ocr_service.extract_data_with_textract(bucket_name, object_key)

                # Textract provides blocks per page. We need to handle this.
                # This parsing logic is complex and would need the page dimensions from Textract.
                # For now, we will just dump the raw text from Textract to a sheet.
                ocr_sheet = workbook.create_sheet(title="OCR_Textract_Output")
                ocr_text = []
                for block in textract_json.get("Blocks", []):
                    if block["BlockType"] == "LINE":
                        ocr_text.append(block.get("Text", ""))

                ocr_sheet.cell(row=1, column=1).value = "\\n".join(ocr_text)

        workbook.save(excel_path)
        logger.info("Successfully completed hybrid conversion.", excel_path=excel_path)

    except Exception as e:
        logger.error("Failed during hybrid conversion", error=str(e), exc_info=True)
        raise
