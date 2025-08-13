import pdfplumber
import openpyxl
from openpyxl.utils import get_column_letter
import structlog
from typing import List, Dict, Any
import statistics

logger = structlog.get_logger(__name__)

Element = Dict[str, Any]

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

def map_elements_to_sheet(sheet, elements: List[Element], page_width: float):
    """
    Maps extracted elements onto an Excel sheet, including layout formatting
    like merged cells, using a more robust while loop.
    """
    if not elements:
        return

    avg_char_width = statistics.mean((el['x1'] - el['x0']) / len(el['text']) for el in elements if el['text']) if elements else 10

    lines = {}
    for el in elements:
        line_key = round(el["top"] / 5) * 5
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(el)

    sorted_lines = sorted(lines.items())
    for row_idx, (_, line_elements) in enumerate(sorted_lines, start=1):
        line_elements.sort(key=lambda el: el["x0"])

        i = 0
        while i < len(line_elements):
            el = line_elements[i]

            # Check if the cell is already part of a merged range from a previous iteration
            # This can happen if the column estimation is not perfect.
            try:
                cell = sheet.cell(row=row_idx, column=int(el["x0"] / (avg_char_width * 1.5)) + 1)
                if isinstance(cell, openpyxl.cell.cell.MergedCell):
                    i += 1
                    continue
            except Exception:
                # This can happen if cell coordinates are invalid, just skip
                i+= 1
                continue


            # Heuristic: if the next word is very close, merge with it.
            is_mergable = False
            if i + 1 < len(line_elements):
                next_el = line_elements[i+1]
                gap = next_el["x0"] - el["x1"]
                if gap < (avg_char_width * 1.5):
                    is_mergable = True

            if is_mergable:
                merged_text_elements = [el]
                end_el = el
                j = i + 1
                while j < len(line_elements):
                    next_el = line_elements[j]
                    if (next_el["x0"] - end_el["x1"]) < (avg_char_width * 1.5):
                        merged_text_elements.append(next_el)
                        end_el = next_el
                        j += 1
                    else:
                        break

                full_text = ' '.join([e["text"] for e in merged_text_elements])

                start_col = int(el["x0"] / (avg_char_width * 1.5)) + 1
                end_col = int(end_el["x1"] / (avg_char_width * 1.5)) + 1

                if start_col <= end_col:
                    sheet.merge_cells(start_row=row_idx, start_column=start_col, end_row=row_idx, end_column=end_col)
                    sheet.cell(row=row_idx, column=start_col).value = full_text

                i = j # Advance the main loop counter past the merged elements
            else:
                # Not mergable, place single word
                col_idx = int(el["x0"] / (avg_char_width * 1.5)) + 1
                sheet.cell(row=row_idx, column=col_idx).value = el["text"]
                i += 1


def convert_pdf_to_excel(pdf_path: str, excel_path: str):
    """
    Creates an Excel file with one sheet per PDF page, attempting to
    reconstruct the layout with merged cells.
    """
    logger.info("Starting layout-aware conversion with merging", pdf_path=pdf_path)

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

                map_elements_to_sheet(sheet, page_elements, float(page.width))

        workbook.save(excel_path)
        logger.info("Successfully created Excel file with layout formatting.", excel_path=excel_path)

    except Exception as e:
        logger.error("Failed during layout-aware conversion", error=str(e), exc_info=True)
        raise
