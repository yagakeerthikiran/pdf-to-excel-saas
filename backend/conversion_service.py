import pdfplumber
import openpyxl
from openpyxl.utils import get_column_letter
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger(__name__)

Element = Dict[str, Any]

def extract_elements_from_page(page) -> List[Element]:
    """
    Extracts all text words from a single PDF page with their bounding boxes.
    """
    words = page.extract_words(
        x_tolerance=1.5,
        y_tolerance=1.5,
        keep_blank_chars=False,
        use_text_flow=True,
        horizontal_ltr=True
    )
    return [{
        "text": str(word["text"]),
        "x0": float(word["x0"]),
        "top": float(word["top"]),
        "x1": float(word["x1"]),
        "bottom": float(word["bottom"]),
    } for word in words]

def map_elements_to_sheet(sheet, elements: List[Element], page_width: float, page_height: float):
    """
    Maps extracted elements onto an Excel sheet by grouping words into phrases,
    placing them in single cells, and using a more robust column detection logic.
    """
    if not elements:
        return

    # --- 1. Final Column Detection Heuristic ---
    all_x0s = sorted([el["x0"] for el in elements])
    column_clusters = []
    if all_x0s:
        current_cluster = [all_x0s[0]]
        for x0 in all_x0s[1:]:
            # If the next x0 is close to the last one, add it to the current cluster
            if x0 < current_cluster[-1] + 10: # 10-point tolerance
                current_cluster.append(x0)
            else:
                # Otherwise, finalize the old cluster and start a new one
                column_clusters.append(current_cluster)
                current_cluster = [x0]
        column_clusters.append(current_cluster) # Add the last cluster

    # The final column positions are the average of each cluster
    column_positions = sorted([sum(cluster) / len(cluster) for cluster in column_clusters])

    def get_col_idx(x0):
        # Find the column that an x-coordinate belongs to
        for i, pos in enumerate(column_positions, start=1):
            if x0 < pos + 5: # Allow a small tolerance
                return i
        return len(column_positions) + 1

    # --- 2. Group elements by line ---
    lines = {}
    for el in elements:
        line_key = round(el["top"] / 5) * 5
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(el)

    # --- 3. Place elements onto the grid ---
    sorted_lines = sorted(lines.items())
    for row_idx, (_, line_elements) in enumerate(sorted_lines, start=1):
        line_elements.sort(key=lambda el: el["x0"])

        i = 0
        while i < len(line_elements):
            start_element = line_elements[i]

            phrase_elements = [start_element]
            j = i + 1
            while j < len(line_elements):
                prev_el = phrase_elements[-1]
                current_el = line_elements[j]
                gap = current_el["x0"] - prev_el["x1"]
                v_overlap = (min(prev_el["bottom"], current_el["bottom"]) - max(prev_el["top"], current_el["top"])) > 0
                if gap < 8 and v_overlap:
                    phrase_elements.append(current_el)
                    j += 1
                else:
                    break

            full_phrase = ' '.join([e["text"] for e in phrase_elements])
            start_col_idx = get_col_idx(start_element["x0"])

            cell_to_write = sheet.cell(row=row_idx, column=start_col_idx)
            if isinstance(cell_to_write, openpyxl.cell.cell.MergedCell):
                logger.warn("Skipping element due to merged cell overlap", phrase=full_phrase, row=row_idx, col=start_col_idx)
                i = j
                continue

            end_col_idx = get_col_idx(phrase_elements[-1]["x1"])

            if end_col_idx > start_col_idx:
                sheet.merge_cells(start_row=row_idx, start_column=start_col_idx, end_row=row_idx, end_column=end_col_idx)

            sheet.cell(row=row_idx, column=start_col_idx).value = full_phrase
            i = j

    for i in range(1, sheet.max_column + 1):
        sheet.column_dimensions[get_column_letter(i)].auto_size = True

def convert_pdf_to_excel(pdf_path: str, excel_path: str):
    """
    Creates an Excel file with one sheet per PDF page, reconstructing phrases.
    """
    logger.info("Starting phrase reconstruction conversion", pdf_path=pdf_path)

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
        logger.info("Successfully created Excel file with phrase reconstruction.", excel_path=excel_path)

    except Exception as e:
        logger.error("Failed during phrase reconstruction conversion", error=str(e), exc_info=True)
        raise
