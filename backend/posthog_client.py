import os
import posthog

# Get PostHog credentials from environment variables
key: str = os.environ.get("POSTHOG_API_KEY")
host: str = os.environ.get("POSTHOG_API_HOST", "https://app.posthog.com")

# Initialize the PostHog client
if key:
    posthog.project_api_key = key
    posthog.host = host
else:
    print("Warning: PostHog API Key not found. PostHog client not initialized.")

def get_posthog_client():
    """
    Returns the initialized PostHog client module.
    """
    if not posthog.project_api_key:
        raise ValueError("PostHog client is not initialized. Check your environment variables.")
    return posthog
