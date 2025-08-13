import pdfplumber
import openpyxl
from openpyxl.utils import get_column_letter
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger(__name__)

def convert_pdf_to_excel(pdf_path: str, excel_path: str):
    """
    Extracts tables from a PDF using a hybrid strategy (lines, then text)
    and saves each table to a separate sheet in an Excel file.
    Also extracts all non-table text to a separate sheet.
    """
    logger.info("Starting hybrid (vision/text) conversion", pdf_path=pdf_path)

    try:
        workbook = openpyxl.Workbook()
        if "Sheet" in workbook.sheetnames:
            workbook.remove(workbook["Sheet"])

        with pdfplumber.open(pdf_path) as pdf:
            # --- 1. Extract Full Page Text ---
            text_sheet = workbook.create_sheet(title="All_Text")
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2)
                if text:
                    full_text += text + "\\n\\n--- End of Page " + str(page.page_number) + " ---\\n\\n"
            text_sheet.cell(row=1, column=1).value = full_text

            # --- 2. Extract Tables Using Hybrid Strategy ---
            table_count = 0
            for i, page in enumerate(pdf.pages):

                # First, try the "lines" strategy - most accurate
                line_table_settings = { "vertical_strategy": "lines", "horizontal_strategy": "lines" }
                tables = page.extract_tables(line_table_settings)

                # If no tables found with lines, fall back to the "text" strategy
                if not tables:
                    logger.warn(f"No tables found with 'lines' strategy on page {i+1}. Falling back to 'text' strategy.")
                    text_table_settings = { "vertical_strategy": "text", "horizontal_strategy": "text" }
                    tables = page.extract_tables(text_table_settings)

                for table in tables:
                    table_count += 1
                    table_sheet = workbook.create_sheet(title=f"Table_{table_count}_Page_{i+1}")

                    for r, row_data in enumerate(table, start=1):
                        for c, cell_data in enumerate(row_data, start=1):
                            cleaned_data = str(cell_data).replace('\\n', ' ').strip() if cell_data else ""
                            table_sheet.cell(row=r, column=c).value = cleaned_data

                    for col_idx in range(1, table_sheet.max_column + 1):
                        table_sheet.column_dimensions[get_column_letter(col_idx)].auto_size = True

            if table_count == 0:
                logger.warn("No tables found using any strategy.", pdf_path=pdf_path)

        workbook.save(excel_path)
        logger.info("Successfully created Excel file with hybrid table extraction.", excel_path=excel_path)

    except Exception as e:
        logger.error("Failed during hybrid conversion", error=str(e), exc_info=True)
        raise
