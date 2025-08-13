import os
import glob
import pytest
import openpyxl
from backend.conversion_service import convert_pdf_to_excel
from pypdf.errors import FileNotDecryptedError
from pdfplumber.utils.exceptions import PdfminerException
from botocore.exceptions import NoRegionError

# --- Test Configuration ---
PDF_SAMPLES_DIR = "/tmp/pdf-test-files"
TEST_OUTPUT_DIR = "tests/output"
S3_BUCKET_NAME = "placeholder-bucket"

if os.path.isdir(PDF_SAMPLES_DIR):
    pdf_files = glob.glob(os.path.join(PDF_SAMPLES_DIR, "*.pdf"))
else:
    pdf_files = []

@pytest.fixture(scope="session", autouse=True)
def setup_teardown_session():
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    yield

@pytest.mark.parametrize("pdf_path", pdf_files)
def test_hybrid_conversion_pipeline(pdf_path):
    """
    Tests the full hybrid conversion pipeline on a given PDF file.
    """
    assert os.path.exists(pdf_path), f"Sample PDF not found: {pdf_path}"

    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    excel_path = os.path.join(TEST_OUTPUT_DIR, f"{base_filename}_output.xlsx")

    s3_object_key = f"uploads/{os.path.basename(pdf_path)}"

    try:
        convert_pdf_to_excel(pdf_path, excel_path, S3_BUCKET_NAME, s3_object_key)
    except (FileNotDecryptedError, PdfminerException) as e:
        pytest.skip(f"Skipping un-processable PDF file: {pdf_path}. Reason: {type(e).__name__}")
    except NoRegionError:
        pytest.xfail("Textract call failed due to no AWS region/credentials in test environment, as expected.")
    except Exception as e:
        pytest.fail(f"convert_pdf_to_excel raised an unexpected exception for {pdf_path}: {e}")

    # --- Assertions ---
    assert os.path.exists(excel_path), f"Output Excel file was not created for {pdf_path}"
    assert os.path.getsize(excel_path) > 0, f"The output Excel file for {pdf_path} is empty."

    # --- Specific Assertions for non-OCR files ---
    if "NAB" not in base_filename and "Passport" not in base_filename:
        try:
            workbook = openpyxl.load_workbook(excel_path)
            table_sheets = [name for name in workbook.sheetnames if name.startswith("Table_")]
            assert len(table_sheets) > 0, f"Expected tables to be found for {pdf_path}, but none were."
        except Exception as e:
            pytest.fail(f"Failed to inspect the output Excel file for {pdf_path}: {e}")
