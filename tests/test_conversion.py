import os
import glob
import pytest
import openpyxl
from backend.conversion_service import convert_pdf_to_excel
from pypdf.errors import FileNotDecryptedError
from pdfplumber.utils.exceptions import PdfminerException

# --- Test Configuration ---
PDF_SAMPLES_DIR = "/tmp/pdf-test-files"
TEST_OUTPUT_DIR = "tests/output"

if os.path.isdir(PDF_SAMPLES_DIR):
    pdf_files = glob.glob(os.path.join(PDF_SAMPLES_DIR, "*.pdf"))
else:
    pdf_files = []

@pytest.fixture(scope="session", autouse=True)
def setup_teardown_session():
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    yield

@pytest.mark.parametrize("pdf_path", pdf_files)
def test_layout_reconstruction_pipeline(pdf_path):
    """
    Tests the layout reconstruction pipeline on a given PDF file.
    It will skip tests for encrypted or un-openable PDFs.
    """
    assert os.path.exists(pdf_path), f"Sample PDF not found: {pdf_path}"

    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    excel_path = os.path.join(TEST_OUTPUT_DIR, f"{base_filename}_output.xlsx")

    try:
        convert_pdf_to_excel(pdf_path, excel_path)
    except (FileNotDecryptedError, PdfminerException) as e:
        pytest.skip(f"Skipping un-processable PDF file: {pdf_path}. Reason: {type(e).__name__}")
    except Exception as e:
        pytest.fail(f"convert_pdf_to_excel raised an unexpected exception for {pdf_path}: {e}")

    # --- Assertions ---
    assert os.path.exists(excel_path), f"Output Excel file was not created for {pdf_path}"
    assert os.path.getsize(excel_path) > 0, f"The output Excel file for {pdf_path} is empty."

    # --- Specific Assertions for Kiran_SBI_Statement.pdf ---
    if base_filename == "Kiran_SBI_Statement":
        try:
            workbook = openpyxl.load_workbook(excel_path)
            sheet1 = workbook["Page_1"]

            # Get default dimensions for comparison
            temp_wb = openpyxl.Workbook()
            temp_sheet = temp_wb.active
            default_col_width = temp_sheet.column_dimensions['A'].width
            default_row_height = temp_sheet.row_dimensions[1].height

            # d. Assert that column widths have been set to non-default values
            assert sheet1.column_dimensions['A'].width != default_col_width, "Column A width was not set."

            # e. Assert that row heights have been set to non-default values
            assert sheet1.row_dimensions[1].height != default_row_height, "Row 1 height was not set."

        except Exception as e:
            pytest.fail(f"Failed to inspect the output Excel file for {pdf_path}: {e}")
