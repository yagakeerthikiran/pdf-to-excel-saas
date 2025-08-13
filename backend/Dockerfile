# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies required by camelot-py
# The base image is Amazon Linux, which uses yum.
RUN yum install -y ghostscript

# Copy the requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# We copy everything from the backend directory into the container's working directory
COPY . .

# Set the command to run the handler
# This should match the handler path in serverless.yml (e.g., handler.main)
# The format is <file_name>.<handler_function_name>
CMD [ "handler.handler" ]
