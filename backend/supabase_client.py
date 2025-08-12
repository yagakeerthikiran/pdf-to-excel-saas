import os
from supabase import create_client, Client

# Get Supabase credentials from environment variables
url: str = os.environ.get("SUPABASE_URL")
# For backend operations, we need the service role key to bypass RLS.
key: str = os.environ.get("SUPABASE_SERVICE_KEY")

# Initialize the Supabase client
supabase: Client = None
if url and key:
    supabase = create_client(url, key)
else:
    print("Warning: Supabase URL or Service Key not found. Supabase client not initialized.")

def get_supabase_client() -> Client:
    """
    Returns the initialized Supabase client.
    Raises an exception if the client is not initialized.
    """
    if supabase is None:
        raise ValueError("Supabase client is not initialized. Check your environment variables.")
    return supabase
