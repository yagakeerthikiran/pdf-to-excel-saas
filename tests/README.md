# Tests

This directory contains the testing infrastructure for the application, with a strong focus on the backend conversion logic.

## Purpose
- **Unit & Integration Tests:** Contains tests for individual components and their interactions.
- **PDF Regression Suite:** A critical component of this directory is the `pdf_samples/` subdirectory. It will store an ever-growing collection of PDF documents that have caused issues in the past or represent important edge cases.
- **Auto-Fix Validation:** This test suite is a key part of the "auto-fix" workflow. Before any automated fix is deployed, it must pass all tests here, including a test with the specific PDF that triggered the alert and the entire regression suite. This ensures that a fix for one user's issue does not break functionality for others.
