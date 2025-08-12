from mangum import Mangum
from backend.main import app

# The Mangum handler wraps the FastAPI app, making it compatible with AWS Lambda and API Gateway.
# The `handler` variable is what we point to in serverless.yml.
handler = Mangum(app)
