import pdfplumber
import openpyxl
from openpyxl.utils import get_column_letter
import structlog

logger = structlog.get_logger(__name__)

def convert_pdf_to_excel(pdf_path: str, excel_path: str):
    """
    Extracts tables and text from a PDF and saves them to an Excel file.
    Each table gets its own sheet, and all text is placed on another sheet.
    """
    logger.info("Starting PDF to Excel conversion", pdf_path=pdf_path)

    try:
        workbook = openpyxl.Workbook()
        # Remove the default sheet
        if "Sheet" in workbook.sheetnames:
            workbook.remove(workbook["Sheet"])

        with pdfplumber.open(pdf_path) as pdf:
            # --- Extract and write all text to one sheet ---
            text_sheet = workbook.create_sheet(title="All_Text")
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\\n\\n--- End of Page " + str(page.page_number) + " ---\\n\\n"

            # Write text to a single cell, preserving line breaks
            if full_text:
                text_sheet.cell(row=1, column=1).value = full_text
            else:
                text_sheet.cell(row=1, column=1).value = "No text found in the document."

            # --- Extract and write tables to their own sheets ---
            table_count = 0
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if not tables:
                    continue

                for table in tables:
                    table_count += 1
                    table_sheet = workbook.create_sheet(title=f"Page_{i+1}_Table_{table_count}")

                    for r, row_data in enumerate(table, start=1):
                        for c, cell_data in enumerate(row_data, start=1):
                            table_sheet.cell(row=r, column=c).value = cell_data

                    # Auto-adjust column widths
                    for col_idx in range(1, table_sheet.max_column + 1):
                        column_letter = get_column_letter(col_idx)
                        table_sheet.column_dimensions[column_letter].autosize = True

            if table_count == 0:
                # Create a sheet indicating no tables were found
                workbook.create_sheet(title="No_Tables_Found")

        workbook.save(excel_path)
        logger.info("Successfully converted PDF to Excel", excel_path=excel_path)

    except Exception as e:
        logger.error("Failed to convert PDF to Excel", error=str(e), exc_info=True)
        # Re-raise the exception so the calling function knows about the failure
        raise
