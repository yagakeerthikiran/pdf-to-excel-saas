import structlog
from uuid import UUID
from backend.supabase_client import get_supabase_client

logger = structlog.get_logger(__name__)

def get_profile(user_id: UUID):
    """
    Retrieves a user's profile from the database.
    """
    supabase = get_supabase_client()
    logger.info("Getting profile for user", user_id=str(user_id))
    # response = supabase.table('profiles').select("*").eq('id', user_id).execute()
    # return response.data
    return {"message": f"Profile for {user_id} would be here."}

def increment_conversion_count(user_id: str):
    """
    Increments the free conversion count for a user by calling a database function.
    """
    supabase = get_supabase_client()
    try:
        logger.info("Incrementing conversion count for user", user_id=user_id)
        # This calls a database function to ensure the increment is atomic.
        supabase.rpc('increment_conversions', {'user_id_param': user_id}).execute()
    except Exception as e:
        logger.error("Error incrementing conversion count", user_id=user_id, error=str(e))
        # We don't re-raise here, as failing to increment is not a critical failure
        # for the user's current request, but we must log it.

def update_subscription_status(user_id: str, status: str):
    """
    Updates the subscription status of a user.
    """
    supabase = get_supabase_client()
    try:
        logger.info("Updating subscription status", user_id=user_id, new_status=status)
        response = supabase.table('profiles').update({'subscription_status': status}).eq('id', user_id).execute()
        if len(response.data) == 0:
            logger.warn("No profile found for user_id to update status.", user_id=user_id)
            return None
        return response.data[0]
    except Exception as e:
        logger.error("Error updating subscription status", user_id=user_id, error=str(e))
        return None

def get_usage(user_id: str):
    """
    Gets the current usage stats for a user.
    """
    supabase = get_supabase_client()
    try:
        logger.info("Getting usage for user", user_id=user_id)
        response = supabase.table('profiles').select("free_conversions_used, subscription_status").eq('id', user_id).single().execute()
        return response.data
    except Exception as e:
        logger.error("Error getting usage for user", user_id=user_id, error=str(e))
        return None
