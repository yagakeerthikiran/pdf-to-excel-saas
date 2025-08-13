import pdfplumber
import openpyxl
from openpyxl.utils import get_column_letter
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger(__name__)

Element = Dict[str, Any]
GRID_COLUMNS = 200 # Define a high-resolution virtual grid for mapping

def extract_elements_from_page(page) -> List[Element]:
    """
    Extracts all text words from a single PDF page with their bounding boxes.
    """
    words = page.extract_words(
        x_tolerance=1,
        y_tolerance=1,
        keep_blank_chars=False,
        use_text_flow=True,
        horizontal_ltr=True
    )
    return [{
        "text": word["text"],
        "x0": word["x0"],
        "top": word["top"],
        "x1": word["x1"],
        "bottom": word["bottom"],
    } for word in words]

def map_elements_to_sheet(sheet, elements: List[Element], page_width: float, page_height: float):
    """
    Maps extracted elements onto an Excel sheet using a proportional grid system.
    """
    if not elements:
        return

    # --- 1. Proportional Grid Calculation ---
    # The width of each virtual column in PDF points
    proportional_col_width = page_width / GRID_COLUMNS

    # --- 2. Group elements by line ---
    lines = {}
    for el in elements:
        line_key = round(el["top"] / 5) * 5
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(el)

    # --- 3. Place elements onto the grid ---
    sorted_lines = sorted(lines.items())
    for row_idx, (line_top, line_elements) in enumerate(sorted_lines, start=1):
        line_elements.sort(key=lambda el: el["x0"])

        # Set proportional row height
        # Get the max height of any element in the line
        if line_elements:
            line_height_points = max(el["bottom"] - el["top"] for el in line_elements)
            # Add a little padding
            sheet.row_dimensions[row_idx].height = line_height_points * 1.2

        i = 0
        while i < len(line_elements):
            el = line_elements[i]

            # Use the new proportional mapping
            start_col = int(el["x0"] / proportional_col_width) + 1

            try:
                if isinstance(sheet.cell(row=row_idx, column=start_col), openpyxl.cell.cell.MergedCell):
                    i += 1
                    continue
            except Exception:
                i += 1
                continue

            # Simplified merging logic for now. A more advanced version could handle this better.
            # For this step, we focus on placement. We will refine merging in the next step.
            sheet.cell(row=row_idx, column=start_col).value = el["text"]
            i += 1

    # --- 4. Set Proportional Column Widths ---
    # Convert PDF points to Excel's column width units. This is an approximation.
    # The default font character width is the basis for Excel's unit.
    # A common heuristic is a factor of 5 to 7. Let's start with 6.
    excel_col_width_factor = 6.0
    proportional_excel_col_width = (page_width / GRID_COLUMNS) / excel_col_width_factor

    for i in range(1, sheet.max_column + 1):
        column_letter = get_column_letter(i)
        sheet.column_dimensions[column_letter].width = proportional_excel_col_width

def convert_pdf_to_excel(pdf_path: str, excel_path: str):
    """
    Creates an Excel file with one sheet per PDF page, using a proportional
    grid to reconstruct the layout.
    """
    logger.info("Starting proportional layout conversion", pdf_path=pdf_path)

    try:
        workbook = openpyxl.Workbook()
        if "Sheet" in workbook.sheetnames:
            workbook.remove(workbook["Sheet"])

        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                sheet_name = f"Page_{i+1}"
                logger.info(f"Processing {sheet_name}...")

                sheet = workbook.create_sheet(title=sheet_name)
                page_elements = extract_elements_from_page(page)
                logger.info(f"Found {len(page_elements)} elements on {sheet_name}.")

                map_elements_to_sheet(sheet, page_elements, float(page.width), float(page.height))

        workbook.save(excel_path)
        logger.info("Successfully created Excel file with proportional mapping.", excel_path=excel_path)

    except Exception as e:
        logger.error("Failed during proportional layout conversion", error=str(e), exc_info=True)
        raise
