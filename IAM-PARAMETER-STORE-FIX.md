# Quick IAM Fix for Parameter Store Access

## Issue: IAM user `pdf-to-excel-bot` needs SSM permissions

**Run this command to add Parameter Store permissions:**

```bash
# Create and attach IAM policy for Parameter Store access
aws iam put-user-policy \
  --user-name pdf-to-excel-bot \
  --policy-name ParameterStoreAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ssm:GetParameter",
          "ssm:GetParameters", 
          "ssm:GetParametersByPath",
          "ssm:PutParameter",
          "ssm:DeleteParameter",
          "ssm:DescribeParameters"
        ],
        "Resource": [
          "arn:aws:ssm:ap-southeast-2:654499586766:parameter/pdf-excel-saas/*"
        ]
      }
    ]
  }'
```

## After running this command:

1. **Retry Parameter Store setup:**
   ```powershell
   # Run the PowerShell commands from before
   cd C:\AI\GIT_Repos\pdf-to-excel-saas-clean
   # ... run the parameter setup commands again
   ```

2. **Then trigger a new deployment to fix /api endpoint**

The ALB /api 404 error will be fixed after the next deployment with proper environment variables.