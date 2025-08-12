import os
from fastapi import Depends, HTTPException, Header
import backend.user_service as user_service
import structlog

logger = structlog.get_logger(__name__)

# --- Authentication/User "Simulation" ---

async def get_current_user_id_from_header(x_user_id: str | None = Header(None)) -> str:
    """
    A dependency that simulates getting a user ID from a custom header.
    In a real-world scenario, this would be replaced with a function that
    validates a JWT and extracts the user ID from it.
    """
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="X-User-ID header missing")
    return x_user_id

# --- Main Enforcement Logic ---

FREE_TIER_LIMIT = 5

async def enforce_usage_limits(user_id: str = Depends(get_current_user_id_from_header)):
    """
    A FastAPI dependency that enforces usage limits for free-tier users.
    It depends on getting the user ID from the X-User-ID header.
    """
    logger.info("Enforcing usage limits for user", user_id=user_id)

    usage_data = user_service.get_usage(user_id)

    if not usage_data:
        # If no profile, maybe they just signed up. Allow one action.
        # Or, we could be more strict and require a profile.
        # For now, let's be permissive but log a warning.
        logger.warn("User profile not found for usage check.", user_id=user_id)
        return

    subscription_status = usage_data.get("subscription_status")

    # Pro users are not subject to limits
    if subscription_status != 'free':
        return

    # Check free tier conversion limit
    free_conversions_used = usage_data.get("free_conversions_used", 0)
    if free_conversions_used >= FREE_TIER_LIMIT:
        logger.warn(
            "Free tier limit exceeded for user",
            user_id=user_id,
            conversions_used=free_conversions_used
        )
        raise HTTPException(
            status_code=403,
            detail=f"You have used all {FREE_TIER_LIMIT} of your free conversions. Please upgrade to Pro."
        )

    logger.info("User is within free tier limits", user_id=user_id)
