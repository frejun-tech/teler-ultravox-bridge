import httpx
import asyncio
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

async def get_join_url():
    retries = 0
    max_retries = 5
    
    ULTRAVOX_AGENT_CALL=f"https://api.ultravox.ai/api/agents/{settings.ULTRAVOX_AGENT_ID}/calls"

    payload = {
        "medium": {
            "serverWebSocket": {
                "inputSampleRate": 8000,
                "outputSampleRate": 8000,
                "clientBufferSizeMs": 20000
            }
        }
    }

    headers = {
        "X-API-Key": settings.ULTRAVOX_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        while retries < max_retries:
            try:
                response = await client.post(
                    ULTRAVOX_AGENT_CALL,
                    json=payload,
                    headers=headers
                )
                data = response.json()
                logger.info(f"Initial data from Ultravox: {data}")

                ULTRAVOX_JOIN_URL = data.get("joinUrl")
                if ULTRAVOX_JOIN_URL:
                    logger.info(f"Got joinUrl: {ULTRAVOX_JOIN_URL}")
                    return ULTRAVOX_JOIN_URL  

            except Exception as e:
                logger.error(f"Error contacting Ultravox: {e}")

            retries += 1
            logger.warning(f"Retrying... attempt {retries}/{max_retries}")
            await asyncio.sleep(2)

    logger.error("Failed to get joinUrl from Ultravox after max retries.")
    return None
