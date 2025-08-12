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
Refer to the root `docs/SETUP.md` for instructions on setting up AWS credentials. To deploy the infrastructure, run:

```bash
serverless deploy
```
