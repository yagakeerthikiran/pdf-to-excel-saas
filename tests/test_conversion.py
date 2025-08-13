import os
import glob
import pytest
import openpyxl
from backend.conversion_service import convert_pdf_to_excel
from pypdf.errors import FileNotDecryptedError

# --- Test Configuration ---
PDF_SAMPLES_DIR = "/tmp/pdf-test-files"
TEST_OUTPUT_DIR = "tests/output"

# Find all PDF files in the user-provided directory
if os.path.isdir(PDF_SAMPLES_DIR):
    pdf_files = glob.glob(os.path.join(PDF_SAMPLES_DIR, "*.pdf"))
else:
    pdf_files = []

@pytest.fixture(scope="session", autouse=True)
def setup_teardown_session():
    """
    Fixture to set up the output directory before any tests run
    and leave it for inspection after the run.
    """
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    yield

@pytest.mark.parametrize("pdf_path", pdf_files)
def test_camelot_conversion_pipeline(pdf_path):
    """
    Tests the full conversion pipeline with Camelot on a given PDF file.
    It checks that the process completes and that tables are likely found.
    It will skip tests for encrypted PDFs.
    """
    assert os.path.exists(pdf_path), f"Sample PDF not found: {pdf_path}"

    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    excel_path = os.path.join(TEST_OUTPUT_DIR, f"{base_filename}_output.xlsx")

    try:
        convert_pdf_to_excel(pdf_path, excel_path)
    except FileNotDecryptedError:
        pytest.skip(f"Skipping encrypted PDF file: {pdf_path}")
    except Exception as e:
        pytest.fail(f"convert_pdf_to_excel raised an unexpected exception for {pdf_path}: {e}")

    # --- Assertions ---
    assert os.path.exists(excel_path), f"Output Excel file was not created for {pdf_path}"
    assert os.path.getsize(excel_path) > 0, f"The output Excel file for {pdf_path} is empty."

    try:
        workbook = openpyxl.load_workbook(excel_path)
        sheet_names = workbook.sheetnames
        table_sheets = [name for name in sheet_names if name.startswith("Table_")]

        print(f"Found {len(table_sheets)} table sheets in the output for {pdf_path}.")
        assert "All_Text" in sheet_names

    except Exception as e:
        pytest.fail(f"Failed to open and inspect the output Excel file for {pdf_path}: {e}")
