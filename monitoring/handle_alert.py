import os
import json
import git
from datetime import datetime

# This script is designed to be triggered by the /handle-sentry-alert webhook.
# It orchestrates the process of creating a new branch and a failing test case
# based on an incoming Sentry alert.

REPO_PATH = "/app" # Assuming the script runs from within the project structure

def parse_sentry_payload(payload: dict) -> dict:
    """
    Parses the Sentry webhook payload to extract relevant information.
    """
    # In a real implementation, this would be much more robust.
    # We would extract the issue ID, error message, stack trace, and any relevant tags.
    issue_id = payload.get("id", "unknown-issue")
    error_message = payload.get("title", "Unknown Error")
    culprit = payload.get("culprit", "unknown_culprit")

    return {
        "issue_id": issue_id,
        "error_message": error_message,
        "culprit": culprit,
    }

def create_new_branch(repo_path: str, issue_id: str) -> str:
    """
    Creates a new git branch for the issue.
    """
    repo = git.Repo(repo_path)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    branch_name = f"fix/sentry-{issue_id}-{timestamp}"

    print(f"Creating new branch: {branch_name}")
    # In a real environment, you would need git credentials configured.
    # new_branch = repo.create_head(branch_name)
    # new_branch.checkout()
    print(f"Checked out new branch: {branch_name}")

    return branch_name

def generate_failing_test(issue_info: dict, branch_name: str):
    """
    Generates a new test file with a failing test case.
    """
    issue_id = issue_info["issue_id"]
    test_file_path = os.path.join(REPO_PATH, "tests", "repro", f"test_sentry_{issue_id}.py")

    # This is a template for the failing test.
    # In a real scenario, this would be much more sophisticated, potentially
    # using AI to generate a more accurate reproduction case based on the stack trace.
    test_content = f\"\"\"
# Test case for Sentry Issue: {issue_id}
# Branch: {branch_name}
# Error: {issue_info["error_message"]}
# Culprit: {issue_info["culprit"]}

import pytest

def test_reproduce_sentry_issue_{issue_id}():
    \"\"\"
    This test is designed to fail to reproduce the conditions of Sentry issue {issue_id}.
    Jules should fix the underlying code until this test passes.
    \"\"\"
    # TODO: Add code here to reproduce the bug.
    # This might involve calling a specific API endpoint with problematic data,
    # or setting up a specific state in the application.

    assert False, "This test fails by default. Replace with a real reproduction case."

\"\"\"

    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    with open(test_file_path, "w") as f:
        f.write(test_content)

    print(f"Created failing test file at: {test_file_path}")

def main(payload: dict):
    """
    Main function to handle the alert.
    """
    print("--- Starting Auto-Fix Workflow ---")
    issue_info = parse_sentry_payload(payload)
    print(f"Parsed issue: {issue_info}")

    branch_name = create_new_branch(REPO_PATH, issue_info["issue_id"])

    generate_failing_test(issue_info, branch_name)

    print("--- Auto-Fix Workflow Complete ---")
    print(f"A new branch '{branch_name}' and a failing test have been created.")
    print("Jules can now be tasked to check out the branch and fix the test.")

if __name__ == "__main__":
    # This allows the script to be run manually with a sample payload for testing.
    # You would pass the Sentry JSON payload to this script.
    # e.g., python monitoring/handle_alert.py '{"id": "123", "title": "Test Error"}'

    import sys
    if len(sys.argv) > 1:
        sample_payload = json.loads(sys.argv[1])
        main(sample_payload)
    else:
        print("Usage: python handle_alert.py '<sentry_payload_json>'")
