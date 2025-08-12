import os
import pytest
from backend.conversion_service import convert_pdf_to_excel

# Define the paths relative to the project root
SAMPLE_PDF_PATH = "tests/pdf_samples/sample.pdf"
TEST_OUTPUT_DIR = "tests/output"
TEST_EXCEL_PATH = os.path.join(TEST_OUTPUT_DIR, "test_output.xlsx")

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """
    Fixture to set up the output directory before tests run
    and clean it up after tests run.
    """
    # Setup: create output directory
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    yield # this is where the testing happens

    # Teardown: clean up generated files
    if os.path.exists(TEST_EXCEL_PATH):
        os.remove(TEST_EXCEL_PATH)
    # Clean up the directory if it's empty
    if os.path.exists(TEST_OUTPUT_DIR) and not os.listdir(TEST_OUTPUT_DIR):
        os.rmdir(TEST_OUTPUT_DIR)

def test_pdf_to_excel_pipeline():
    """
    Tests that the convert_pdf_to_excel function runs without errors
    and produces an output file. This is a basic pipeline/smoke test.
    """
    # Check if the sample PDF exists before running the test
    assert os.path.exists(SAMPLE_PDF_PATH), f"Sample PDF not found at {SAMPLE_PDF_PATH}"

    try:
        # Call the function under test
        convert_pdf_to_excel(SAMPLE_PDF_PATH, TEST_EXCEL_PATH)
    except Exception as e:
        pytest.fail(f"convert_pdf_to_excel raised an unexpected exception: {e}")

    # Assert that the output file was created
    assert os.path.exists(TEST_EXCEL_PATH), f"Output Excel file was not created at {TEST_EXCEL_PATH}"

    # Optional: A very basic check on the output file
    assert os.path.getsize(TEST_EXCEL_PATH) > 0, "The output Excel file is empty."
