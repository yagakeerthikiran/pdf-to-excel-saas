import json
import pytest
from backend.conversion_service import parse_textract_blocks, build_grid_from_elements

# A sample mock of an AWS Textract JSON response for a single page.
# This represents a simple 2x3 table:
# Date        Description      Amount
# 2023-01-15  Coffee Shop      $5.00
MOCK_TEXTRACT_JSON = """
{
  "Blocks": [
    {
      "BlockType": "WORD", "Text": "Date", "Page": 1,
      "Geometry": {"BoundingBox": {"Left": 0.1, "Top": 0.1, "Width": 0.1, "Height": 0.05}}
    },
    {
      "BlockType": "WORD", "Text": "Description", "Page": 1,
      "Geometry": {"BoundingBox": {"Left": 0.4, "Top": 0.1, "Width": 0.2, "Height": 0.05}}
    },
    {
      "BlockType": "WORD", "Text": "Amount", "Page": 1,
      "Geometry": {"BoundingBox": {"Left": 0.8, "Top": 0.1, "Width": 0.15, "Height": 0.05}}
    },
    {
      "BlockType": "WORD", "Text": "2023-01-15", "Page": 1,
      "Geometry": {"BoundingBox": {"Left": 0.1, "Top": 0.2, "Width": 0.2, "Height": 0.05}}
    },
    {
      "BlockType": "WORD", "Text": "Coffee", "Page": 1,
      "Geometry": {"BoundingBox": {"Left": 0.4, "Top": 0.2, "Width": 0.12, "Height": 0.05}}
    },
    {
      "BlockType": "WORD", "Text": "Shop", "Page": 1,
      "Geometry": {"BoundingBox": {"Left": 0.53, "Top": 0.2, "Width": 0.08, "Height": 0.05}}
    },
    {
      "BlockType": "WORD", "Text": "$5.00", "Page": 1,
      "Geometry": {"BoundingBox": {"Left": 0.8, "Top": 0.2, "Width": 0.1, "Height": 0.05}}
    }
  ]
}
"""

def test_parse_textract_blocks():
    """
    Tests that the parser correctly converts proportional coordinates to absolute ones.
    """
    textract_data = json.loads(MOCK_TEXTRACT_JSON)
    page_width, page_height = 1000, 800

    elements = parse_textract_blocks(textract_data, page_width, page_height)

    assert len(elements) == 7

    # Check the first element ("Date")
    date_el = elements[0]
    assert date_el['text'] == "Date"
    assert date_el['x0'] == pytest.approx(0.1 * page_width)
    assert date_el['top'] == pytest.approx(0.1 * page_height)
    assert date_el['x1'] == pytest.approx((0.1 + 0.1) * page_width)
    assert date_el['bottom'] == pytest.approx((0.1 + 0.05) * page_height)
    assert date_el['height'] == pytest.approx(0.05 * page_height)

def test_build_grid_from_elements():
    """
    Tests the layout analysis function to ensure it correctly builds a grid.
    """
    textract_data = json.loads(MOCK_TEXTRACT_JSON)
    page_width, page_height = 1000, 800

    # First, run the data through the parser
    elements = parse_textract_blocks(textract_data, page_width, page_height)

    # Now, test the grid builder
    grid = build_grid_from_elements(elements)

    # We expect 2 rows and 3 columns
    assert len(grid) == 2, "Should detect 2 lines"
    assert all(len(row) == 3 for row in grid), "Each row should have 3 columns"

    # Check the content of the grid
    expected_grid = [
        ['Date', 'Description', 'Amount'],
        ['2023-01-15', 'Coffee Shop', '$5.00']
    ]

    # The word "Coffee" and "Shop" should be merged into one cell
    assert grid[1][1] == "Coffee Shop"

    assert grid == expected_grid


def test_parse_textract_blocks_with_none():
    """parse_textract_blocks should gracefully handle None input."""
    # When textract_json is None, the function should simply return an empty list
    elements = parse_textract_blocks(None, 1000, 800)
    assert elements == []
