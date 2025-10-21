# Teler Ultravox Bridge

A reference integration between **Teler** and **Ultravox**, based on media streaming over WebSockets.

## About

This project is a reference implementation to bridge **Teler** and **Ultravox**. It enables real-time media streaming over WebSockets, facilitating live audio interactions.

---

## Features

- Post request to Ultravox to get the Join URL (websocket URL)
- Real-time streaming of media via WebSockets
- Bi-directional communication between Teler client and Ultravox
- Sample structure for deployment (Docker, environment variables)
- Basic error handling and connection management

---

### Prerequisites

Ensure you have the following installed / available:

- Docker
- Valid API credentials / access:
  - Teler account / API key / endpoints (frejun account)
  - Ultravox API access

---

## Setup

1. **Clone and configure:**

   ```bash
   git clone https://github.com/frejun-tech/teler-ultravox-bridge.git
   cd teler-ultravox-bridge
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Run with Docker:**
   ```bash
   docker compose up --build
   ```

## Environment Variables

| Variable            | Description            | Default  |
| ------------------- | ---------------------- | -------- |
| `ULTRAVOX_API_KEY`  | Your Ultravox API key  | Required |
| `ULTRAVOX_AGENT_ID` | Your Ultravox Agent ID | Required |
| `TELER_API_KEY`     | Your Teler API key     | Required |
| `NGROK_AUTHTOKEN`   | Your ngrok auth token  | Required |

## API Endpoints

- `GET /` - Health check with server domain
- `GET /health` - Service status
- `GET /ngrok-status` - Current ngrok status and URL
- `POST /api/v1/calls/initiate-call` - Start a new call with dynamic phone numbers
- `POST /api/v1/calls/flow` - Get call flow configuration
- `WebSocket /api/v1/calls/media-stream` - Audio streaming between teler and ultravox
- `POST /api/v1/webhooks/receiver` - Teler → Ultravox webhook receiver

### Call Initiation Example

```bash
curl -X POST "http://localhost:8000/api/v1/calls/initiate-call" \
  -H "Content-Type: application/json" \
  -d '{
    "from_number": "+1234567890",
    "to_number": "+0987654321"
  }'
```
