import json
import base64
import logging
from fastapi import WebSocket
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

async def teler_to_ultravox(ultravox_join_url, websocket: WebSocket):
    """
    Receive base64-encoded audio chunks from Teler and forward to Ultravox as raw bytes of 8 kHz PCM Linear16.
    """
    try:
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                if data.get("type") != "audio":
                    continue

                audio_b64 = data["data"]["audio_b64"]
                logger.info(f"[media-stream][teler] Received audio chunk ({len(audio_b64)} base64 chars)")
                
                raw_audio_bytes = base64.b64decode(audio_b64)
                
                logger.info(f"Sending {len(raw_audio_bytes)} bytes to Ultravox")
                await ultravox_join_url.send(raw_audio_bytes)
                logger.info(f"[media-stream][teler] Sent {len(raw_audio_bytes)} bytes to Ultravox")
            
            except Exception as e:
                logger.info(f"[media-stream][teler] Audio processing error: {type(e).__name__}: {e}")
                raise  

    except Exception as e:
        logger.info(f"[media-stream][teler] Fatal error: {type(e).__name__}: {e}")
        raise