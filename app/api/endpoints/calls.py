import json
import asyncio
import logging
import time

import websockets
from fastapi import (APIRouter, HTTPException, WebSocket, status)
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect, WebSocketState
from pydantic import BaseModel
from app.utils.get_join_url import get_join_url

from app.core.config import settings
from app.utils.teler_to_ultravox import teler_to_ultravox
from app.utils.ultravox_to_teler import ultravox_to_teler
from app.utils.teler_client import TelerClient

logger = logging.getLogger(__name__)
router = APIRouter()

class CallFlowRequest(BaseModel):
    call_id: str
    account_id: str
    from_number: str
    to_number: str

class CallRequest(BaseModel):
    from_number: str
    to_number: str

@router.get("/")
async def root():
    return {"message": "Welcome to the Teler-ultravox bridge"}

@router.post("/flow", status_code=status.HTTP_200_OK, include_in_schema=False)
async def stream_flow(payload: CallFlowRequest):
    """
    Return stream flow as JSON Response containing websocket url to connect
    """
    ws_url = f"wss://{settings.SERVER_DOMAIN}/api/v1/calls/media-stream"
    stream_flow = {
        "action": "stream",
        "ws_url": ws_url,
        "chunk_size": 1200,
        "sample_rate": "8k",  
        "record": True
    }
    return JSONResponse(stream_flow)

@router.post("/initiate-call", status_code=status.HTTP_200_OK)
async def initiate_call(call_request: CallRequest):
    """
    Initiate a call using Teler SDK.
    """
    try:
        if not settings.ULTRAVOX_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ultravox_API_KEY not configured"
            )
        teler_client = TelerClient(api_key=settings.TELER_API_KEY)
        call = await teler_client.create_call(
            from_number=call_request.from_number,
            to_number=call_request.to_number,
            flow_url=f"https://{settings.SERVER_DOMAIN}/api/v1/calls/flow",
            status_callback_url=f"https://{settings.SERVER_DOMAIN}/api/v1/webhooks/receiver",
            record=True,
        )
        logger.info(f"Call created: {call}")
        return JSONResponse(content={"success": True, "call_id": call.id})
    except Exception as e:
        logger.error(f"Failed to create call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Call creation failed."
        )

@router.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """
    Handle received and sent audio chunks, Teler -> Ultravox, Ultravox -> Teler
    """
    await websocket.accept()
    logger.info("Bridge Web Socket Connected")

    ultravox_join_url = None  

    try:
        if not settings.ULTRAVOX_API_KEY:
            await websocket.close(code=1008, reason="ULTRAVOX API KEY not configured")
            return
            
        ULTRAVOX_JOIN_URL = await get_join_url()

        if not ULTRAVOX_JOIN_URL:
            await websocket.close(code=1008, reason="ULTRAVOX Join URL not configured")
            return
        
        async with websockets.connect(
            ULTRAVOX_JOIN_URL
        ) as ultravox_join_url:
            logger.info("[media-stream] Successfully connected to Ultravox WebSocket")

            recv_task = asyncio.create_task(
                teler_to_ultravox(ultravox_join_url, websocket), 
                name="teler_to_ultravox"
            )
            send_task = asyncio.create_task(
                ultravox_to_teler(ultravox_join_url, websocket),
                name="ultravox_to_teler"
            )

            try:
                done, pending = await asyncio.wait(
                    [recv_task, send_task],
                    return_when=asyncio.FIRST_COMPLETED  
                )

                for task in done:
                    if task.exception():
                        logger.error(f"Task {task.get_name()} failed: {task.exception()}")
                    else:
                        logger.debug(f"Task {task.get_name()} completed successfully")

                for task in pending:
                    logger.error(f"Canceling task {task.get_name()}")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            except Exception as e:
                logger.error(f"Error in task handling: {type(e).__name__}: {e}")


    except WebSocketDisconnect:
        logger.error("[media-stream] Teler WebSocket disconnected — closing Ultravox connection...")
        if ultravox_join_url and not ultravox_join_url.closed:
            await ultravox_join_url.close()
            logger.info("[media-stream] Ultravox connection closed after Teler disconnect")

    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"[media-stream] WebSocket connection failed with status {e.status_code}: {e}")
        if e.status_code == 403:
            logger.error("[media-stream] Invalid API key or permission issue.")
    except Exception as e:
        logger.error(f"[media-stream] Top-level error: {type(e).__name__}: {e}")
    finally:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
        logger.info("[media-stream] Connection closed.")
