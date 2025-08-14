# Infrastructure

This directory contains the Infrastructure as Code (IaC) definitions for the project, managed by the Serverless Framework.

## Key Technologies
- Serverless Framework
- AWS CloudFormation

## Purpose
The `serverless.yml` file in this directory defines all the necessary cloud resources, including:
- AWS Lambda functions
- API Gateway endpoints
- IAM roles and permissions
- S3 bucket configurations
- CloudWatch logging and alerts

## Deployment

Before deploying, you must have all your backend credentials and configurations set up in the `backend/.env` file, as described in the main `docs/SETUP.md` guide.

The Serverless Framework needs these variables to be present in the same directory as the `serverless.yml` file.

**Deployment Steps:**

1.  **Copy the environment file:** From the project root, copy the backend environment file into this `infra/` directory.
    ```bash
    # On Linux/macOS
    cp backend/.env infra/
    # On Windows
    copy backend\\.env infra\\.env
    ```

2.  **Navigate to the infra directory:**
    ```bash
    cd infra
    ```

3.  **Deploy the service:**
    ```bash
    serverless deploy
    ```
