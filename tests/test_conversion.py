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
def test_phrase_reconstruction_pipeline(pdf_path):
    """
    Tests the phrase reconstruction pipeline on a given PDF file.
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

            # a. Verify that a specific phrase exists in a single cell
            found_phrase = False
            for row in sheet1.iter_rows():
                for cell in row:
                    if cell.value and "Account Statement from" in str(cell.value):
                        found_phrase = True
                        break
                if found_phrase:
                    break
            assert found_phrase, "The phrase 'Account Statement from' was not found in a single cell."

            # b. Verify that the number of columns is reasonable
            assert sheet1.max_column < 35, f"Expected a reasonable number of columns (< 35), but got {sheet1.max_column}."

        except Exception as e:
            pytest.fail(f"Failed to inspect the output Excel file for {pdf_path}: {e}")
