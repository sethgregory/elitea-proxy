# ELITEA Proxy Service

A secure Flask-based proxy service that translates Claude Code requests to the ELITEA API. This proxy handles authentication header conversion, strips unsupported parameters, maps model names, and provides token counting functionality.

## Features

- **Secure Configuration**: Environment-based configuration with no hardcoded secrets
- **Model Mapping**: Automatic mapping between Claude Code and ELITEA model names
- **Parameter Filtering**: Strips unsupported parameters like `thinking` and `anthropic_beta`
- **Token Estimation**: Local token counting to avoid unnecessary API calls
- **Health Monitoring**: Health check endpoint with ELITEA connectivity testing
- **Comprehensive Logging**: Structured logging with configurable levels
- **Streaming Support**: Full support for streaming responses

## Quick Start

### 1. Set Up Python Environment (Recommended)

Create a virtual environment to avoid dependency conflicts:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

#### Get Your ELITEA Token

To use this proxy, you need an ELITEA API token. Follow these steps to generate one:

1. **Visit the ELITEA Dashboard**: Go to https://next.elitea.ai
2. **Sign in or Create an Account**: If you don't have an account, you'll need to register first
3. **Navigate to API Keys**: Look for an "API Keys", "Tokens", or "Authentication" section in your dashboard
4. **Generate New Token**: Create a new JWT authentication token for API access
5. **Copy the Token**: Save the generated token securely - you'll need it for the configuration below

**Note**: Keep your token secure and never share it publicly. The token provides access to your ELITEA account and API usage.

#### Set Up Environment File
Copy the example environment file and add your ELITEA token:

```bash
cp .env.example .env
```

Edit the `.env` file with your preferred text editor:

```bash
nano .env  # or vim .env, or code .env
```

Replace `your_elitea_jwt_token_here` with your actual ELITEA token:

```
ELITEA_TOKEN=your_actual_elitea_jwt_token_here
```

**Example `.env` file:**
```
# Required
ELITEA_TOKEN=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...

# Optional (shown with defaults)
SERVER_PORT=4000
LOG_LEVEL=INFO
```

### 4. Start the Server

```bash
python elitea-proxy.py
```

The server will start on `http://localhost:4000` by default. You'll first see a colorful ASCII art banner for "Claude-Elitea Proxy", followed by startup information like:

```
2024-XX-XX XX:XX:XX,XXX - elitea-proxy - INFO - Starting ELITEA proxy server on http://0.0.0.0:4000
2024-XX-XX XX:XX:XX,XXX - elitea-proxy - INFO - Forwarding requests to: https://next.elitea.ai/llm/v1
```

## Docker Quick Start

### Prerequisites
- Docker and Docker Compose installed

### Run with Docker Compose (Recommended)

1. **Set up your environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set your ELITEA_TOKEN
   ```

2. **Start the service:**
   ```bash
   docker-compose up -d
   ```

3. **Check status:**
   ```bash
   docker-compose ps
   curl http://localhost:4000/health
   ```

4. **Stop the service:**
   ```bash
   docker-compose down
   ```

### Run with Docker directly

```bash
# Build the image
docker build -t elitea-proxy .

# Run the container
docker run -d \
  --name elitea-proxy \
  -p 4000:4000 \
  -e ELITEA_TOKEN=your_elitea_token_here \
  elitea-proxy

# Check logs
docker logs elitea-proxy

# Stop and remove
docker stop elitea-proxy && docker rm elitea-proxy
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

### Required Configuration

| Variable | Description |
|----------|-------------|
| `ELITEA_TOKEN` | JWT token for ELITEA API authentication |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ELITEA_BASE_URL` | `https://next.elitea.ai/llm/v1` | ELITEA API base URL |
| `SERVER_HOST` | `0.0.0.0` | Server bind address |
| `SERVER_PORT` | `4000` | Server port |
| `SERVER_DEBUG` | `false` | Flask debug mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `REQUEST_TIMEOUT` | `30` | ELITEA API request timeout (seconds) |
| `STREAM_CHUNK_SIZE` | `1024` | Streaming response chunk size |
| `TOKEN_ESTIMATION_RATIO` | `4` | Characters per token for estimation |

## API Endpoints

### POST /v1/messages

Proxy endpoint for Claude API messages. Automatically:
- Maps model names to ELITEA equivalents
- Strips unsupported parameters
- Forwards requests to ELITEA API
- Returns streaming responses

### POST /v1/messages/count_tokens

Token counting endpoint that provides local estimation without calling ELITEA API.

### GET /health

Health check endpoint that returns:
- Service status
- ELITEA API connectivity status
- Configuration information

## Model Mappings

The proxy automatically maps these Claude models:

| Claude Code Model | ELITEA Model |
|------------------|------------|
| `claude-haiku-4-5-20251001` | `eu.anthropic.claude-sonnet-4-20250514-v1:0` |
| `claude-sonnet-4-5-20250929` | `eu.anthropic.claude-sonnet-4-20250514-v1:0` |
| `eu.anthropic.claude-sonnet-4-20250514-v1:0` | `eu.anthropic.claude-sonnet-4-20250514-v1:0` |

## Security Features

- **No Hardcoded Secrets**: All sensitive data loaded from environment variables
- **Input Validation**: JSON request validation with error handling
- **Safe Error Messages**: Error responses don't expose sensitive information
- **Request Logging**: Comprehensive request/response logging for debugging
- **Timeout Protection**: Configurable timeouts prevent hanging requests

## Development

### Running in Development Mode

```bash
# Method 1: Environment variables
export SERVER_DEBUG=true
export LOG_LEVEL=DEBUG
python elitea-proxy.py

# Method 2: Add to your .env file
echo "SERVER_DEBUG=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env
python elitea-proxy.py
```

### Testing the Service

```bash
# Health check
curl http://localhost:4000/health

# Test message endpoint (requires valid ELITEA_TOKEN)
curl -X POST http://localhost:4000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-haiku-4-5-20251001", "messages": [{"role": "user", "content": "Hello"}]}'

# Test token counting
curl -X POST http://localhost:4000/v1/messages/count_tokens \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello world"}]}'
```

## Logging

The service provides structured logging with configurable levels:

- **INFO**: Request/response information, model mappings, configuration
- **WARNING**: Invalid requests, connectivity issues
- **ERROR**: API failures, unexpected errors
- **DEBUG**: Detailed request/response data, parameter stripping

## Error Handling

The proxy provides appropriate HTTP status codes and error messages:

- **400**: Invalid JSON or malformed requests
- **500**: Internal server errors
- **502**: ELITEA API connectivity issues
- **503**: Health check failures

## Files

- `elitea-proxy.py` - Main application
- `config.py` - Configuration management
- `requirements.txt` - Python dependencies
- `.env.example` - Environment configuration template
- `Dockerfile` - Docker container configuration
- `docker-compose.yml` - Docker Compose service definition
- `.dockerignore` - Files excluded from Docker build
- `README.md` - This documentation

## Troubleshooting

### Common Issues

#### "Missing required environment variables: ELITEA_TOKEN"
- **Cause**: No ELITEA_TOKEN set in environment variables
- **Solution**: Create a `.env` file with your ELITEA token as shown in the setup steps
- **Verify**: Check that `.env` file exists and contains `ELITEA_TOKEN=your_token_here`

#### "Address already in use" / Port 4000 in use
- **Cause**: Another service is running on port 4000
- **Solution**: Either stop the other service or change the port:
  ```bash
  echo "SERVER_PORT=4001" >> .env
  ```

#### "ModuleNotFoundError: No module named 'flask'"
- **Cause**: Dependencies not installed or wrong Python environment
- **Solution**:
  ```bash
  pip install -r requirements.txt
  # Or if using virtual environment:
  source venv/bin/activate && pip install -r requirements.txt
  ```

#### Server starts but health check shows "elitea_status": "connection_failed"
- **Cause**: Invalid ELITEA token or network connectivity issues
- **Solution**:
  - Verify your ELITEA_TOKEN is correct and not expired
  - Check network connectivity to `https://next.elitea.ai`
  - Verify your token has proper permissions

#### "externally-managed-environment" error when installing dependencies
- **Cause**: System Python environment protection (common on Ubuntu 23.04+)
- **Solution**: Use a virtual environment or Docker:
  ```bash
  # Option 1: Virtual environment
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

  # Option 2: Use Docker (recommended)
  docker-compose up -d
  ```

### Debug Mode

For detailed debugging information:

```bash
# In your .env file, add:
SERVER_DEBUG=true
LOG_LEVEL=DEBUG

# Or set temporarily:
SERVER_DEBUG=true LOG_LEVEL=DEBUG python elitea-proxy.py
```

### Verify Setup

Test your installation with these commands:

```bash
# 1. Health check (should return status info)
curl http://localhost:4000/health

# 2. Token counting (should work without ELITEA API)
curl -X POST http://localhost:4000/v1/messages/count_tokens \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'
```

## Support

For issues or questions:

1. **Check the application logs** - The service provides detailed logging
2. **Verify your ELITEA_TOKEN** - Ensure it's valid and not expired
3. **Test network connectivity** - Ensure you can reach the ELITEA API endpoint
4. **Review this troubleshooting section** - Most common issues are covered above

If problems persist, check that all files are present and your environment matches the requirements in this documentation.