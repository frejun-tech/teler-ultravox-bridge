import json
import base64
import logging
from fastapi import WebSocket
from app.core.config import settings
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

async def ultravox_to_teler(ultravox_ws, websocket: WebSocket):
    """
    Receive 8 kHz PCM Linear16 from Ultravox and forward to Teler as base64-encoded audio chunks.
    """
    audio_buffer = b""
    chunk_id = 0
    CHUNK_BUFFER_SIZE = settings.CHUNK_BUFFER_SIZE

    try:
        async for message in ultravox_ws:
            try:
                if isinstance(message, bytes):
                    audio_buffer += message
                    logger.debug(f"[ultravox] Received {len(message)} bytes, buffer={len(audio_buffer)}")

                    if len(audio_buffer) >= CHUNK_BUFFER_SIZE:
                        audio_b64 = base64.b64encode(audio_buffer).decode("utf-8")

                        await websocket.send_json({
                            "type": "audio",
                            "audio_b64": audio_b64,
                            "chunk_id": chunk_id
                        })
                        logger.debug(f"[ultravox] Sent chunk {chunk_id} ({len(audio_buffer)} bytes)")
                        chunk_id += 1
                        audio_buffer = b""

                else:
                    try:
                        message_json = json.loads(message)
                    except json.JSONDecodeError:
                        logger.warning(f"Non-JSON message: {message}")
                        continue

                    msg_type = message_json.get("type")
                    
                    if msg_type == "call_started":
                        call_id = message_json.get("callId")
                        logger.info(f'Call started, call_id: {call_id}')
                        
                    elif msg_type == "transcript":
                        role = message_json.get("role")
                        text = message_json.get("text")
                        logger.debug(f"{role.capitalize()} Conversation: {text}")
                        
                    elif msg_type == "playback_clear_buffer":
                        audio_buffer = b""
                        await websocket.send_json({"type": "clear"})
                        
                    elif msg_type == "state":
                        logger.info(f"State of the agent is: {message_json.get('state')}")
                        
                    else:
                        logger.debug(f"Message: {message_json}")

            except Exception as e:
                logger.error(f"[ultravox] Error processing message: {type(e).__name__}: {e}")

    except ConnectionClosed:
        logger.info("Ultravox WebSocket disconnected")
    finally:
        if audio_buffer:
            audio_b64 = base64.b64encode(audio_buffer).decode("utf-8")
            await websocket.send_json({
                "type": "audio",
                "audio_b64": audio_b64,
                "chunk_id": chunk_id
            })
            logger.debug(f"[ultravox] Sent final chunk {chunk_id} ({len(audio_buffer)} bytes)")
            audio_buffer =  b""

        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
        try:
            await ultravox_ws.close()
        except Exception as e:
            logger.error(f"Error closing Ultravox WebSocket: {type(e).__name__}: {e}")
        logger.debug("ultravox_to_teler task ended")
