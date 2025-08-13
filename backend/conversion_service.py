import pdfplumber
import camelot
import openpyxl
from openpyxl.utils import get_column_letter
import structlog

logger = structlog.get_logger(__name__)

def convert_pdf_to_excel(pdf_path: str, excel_path: str):
    """
    Extracts tables using Camelot and text using pdfplumber from a PDF
    and saves them to an Excel file.
    """
    logger.info("Starting PDF to Excel conversion with Camelot", pdf_path=pdf_path)

    try:
        workbook = openpyxl.Workbook()
        if "Sheet" in workbook.sheetnames:
            workbook.remove(workbook["Sheet"])

        # --- 1. Extract tables with Camelot ---
        # Camelot is highly effective at table extraction.
        # We use the 'stream' flavor which is good for PDFs without clear table lines.
        # 'lattice' is better for tables with clear lines. We could make this configurable.
        logger.info("Reading tables with Camelot...")
        tables = camelot.read_pdf(pdf_path, flavor='stream', pages='all')

        if tables.n > 0:
            logger.info(f"Found {tables.n} tables with Camelot.")
            for i, table in enumerate(tables):
                table_sheet = workbook.create_sheet(title=f"Table_{i+1}")
                for r, row in enumerate(table.df.itertuples(), start=1):
                    for c, cell_data in enumerate(row, start=1):
                        # itertuples includes an index, so we skip it (c-1)
                        if c > 1:
                            table_sheet.cell(row=r, column=c-1).value = cell_data

                # Auto-adjust column widths
                for col_idx in range(1, table_sheet.max_column + 1):
                    column_letter = get_column_letter(col_idx)
                    table_sheet.column_dimensions[column_letter].autosize = True
        else:
            logger.info("No tables found by Camelot.")
            workbook.create_sheet(title="No_Tables_Found")

        # --- 2. Extract full text with pdfplumber ---
        # pdfplumber is excellent for raw text extraction.
        logger.info("Extracting text with pdfplumber...")
        with pdfplumber.open(pdf_path) as pdf:
            text_sheet = workbook.create_sheet(title="All_Text")
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\\n\\n--- End of Page " + str(page.page_number) + " ---\\n\\n"

            if full_text:
                text_sheet.cell(row=1, column=1).value = full_text
            else:
                text_sheet.cell(row=1, column=1).value = "No text found in the document."

        workbook.save(excel_path)
        logger.info("Successfully converted PDF to Excel", excel_path=excel_path)

    except Exception as e:
        logger.error("Failed to convert PDF to Excel", error=str(e), exc_info=True)
        raise
