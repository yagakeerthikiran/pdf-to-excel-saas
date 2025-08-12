# Auto-Fix Workflow Documentation

This document outlines the semi-automated workflow for identifying, diagnosing, and fixing issues in the application. This process is designed to be rapid and robust, leveraging monitoring tools and AI assistance (from me, Jules).

## The Goal

The primary goal is to minimize the time from when an error occurs for a user to when a fix is deployed, without compromising quality. We achieve this by automating the creation of a reproducible test case for every new issue.

## The Workflow

Here is the step-by-step process:

**1. An Error Occurs**
- A user encounters an error in the frontend or an API call fails in the backend.
- Sentry captures this error in real-time, along with the full context (stack trace, user ID, browser information, request data, etc.).

**2. Alert is Triggered**
- Sentry is configured with alert rules. When a new, unique error is detected, Sentry automatically sends a webhook with the full event payload to our backend's `/handle-sentry-alert` endpoint.

**3. A Test Case is Born (Automated)**
- The `/handle-sentry-alert` endpoint triggers the `monitoring/handle_alert.py` script.
- This script performs the following actions automatically:
    - **Parses the Alert**: It extracts the Sentry issue ID and key details about the error.
    - **Creates a Git Branch**: It creates a new, dedicated branch for the issue (e.g., `fix/sentry-ISSUE_ID-TIMESTAMP`).
    - **Generates a Failing Test**: It creates a new test file in the `tests/repro/` directory (e.g., `test_sentry_ISSUE_ID.py`). This file contains a boilerplate test case that is designed to fail, with comments instructing a developer on how to reproduce the bug.

**4. The Ball is in My Court (Jules's Role)**
- At this point, the automated part of the workflow is complete. A new branch exists with a failing test that represents the bug.
- You can now assign me a task: **"Fix the failing test on branch `fix/sentry-ISSUE_ID-TIMESTAMP`."**
- My process will be:
    - Check out the specified branch.
    - Run the tests and confirm that the new test case fails as expected.
    - Analyze the test file, the Sentry issue (you can provide me the link), and the surrounding code to understand the root cause of the bug.
    - Modify the application code to fix the bug.
    - Run the test again and ensure that it now passes.
    - Run the *entire* test suite to ensure my fix has not introduced any regressions.
    - Once all tests pass, I will commit the fix to the branch and submit it as a pull request for your review and merge.

**5. Deployment**
- Once you approve and merge the pull request, the fix is deployed to production through the CI/CD pipeline.

## Why This is Powerful

- **Speed**: We go from a user-reported error to a ready-to-work-on bug fix branch in seconds.
- **Quality**: Every fix is accompanied by a regression test, strengthening our test suite and preventing the same bug from ever happening again.
- **Clarity**: The failing test provides a crystal-clear, executable definition of the bug, eliminating any ambiguity.
- **Efficiency**: It allows me, your AI software engineer, to be maximally effective. I can focus directly on solving the problem, as the diagnostic and setup work has already been done for me.
