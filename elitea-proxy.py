#!/usr/bin/env python3
"""
Simple proxy to translate Claude Code requests to ELITEA API.
Handles authentication header conversion and strips unsupported beta flags.
"""

from flask import Flask, request, Response
import requests
import json
import logging
from config import config

try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)  # Initialize colorama
    COLORAMA_AVAILABLE = True
except ImportError:
    # Fallback if colorama is not available
    COLORAMA_AVAILABLE = False
    class Fore:
        CYAN = MAGENTA = YELLOW = GREEN = BLUE = RED = RESET = ''
    class Style:
        BRIGHT = RESET_ALL = ''

app = Flask(__name__)

# Setup logging
logger = config.setup_logging()

@app.route('/v1/messages', methods=['POST'])
def proxy_messages():
    """Proxy /v1/messages requests to ELITEA"""

    try:
        # Get the request body
        body = request.get_json()
        if not body:
            logger.warning("Received request with no JSON body")
            return Response(
                json.dumps({'error': {'message': 'Request body must be valid JSON'}}),
                status=400,
                content_type='application/json'
            )

        logger.info(f"Proxying request for model: {body.get('model', 'unknown')}")

        # Map model name if needed
        if 'model' in body:
            original_model = body['model']
            body['model'] = config.get_mapped_model(original_model)
            if original_model != body['model']:
                logger.info(f"Mapped model {original_model} -> {body['model']}")

        # Remove unsupported parameters
        removed_params = []
        for param in config.UNSUPPORTED_PARAMS:
            if body.pop(param, None) is not None:
                removed_params.append(param)

        if removed_params:
            logger.info(f"Removed unsupported parameters: {removed_params}")

        # Get headers for ELITEA
        headers = config.get_elitea_headers()

        # Forward the request to ELITEA
        response = requests.post(
            f'{config.ELITEA_BASE_URL}/messages',
            json=body,
            headers=headers,
            stream=True,  # Support streaming responses
            timeout=config.REQUEST_TIMEOUT
        )

        logger.info(f"ELITEA response status: {response.status_code}")

        # Return ELITEA's response
        return Response(
            response.iter_content(chunk_size=config.STREAM_CHUNK_SIZE),
            status=response.status_code,
            headers=dict(response.headers)
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to ELITEA failed: {e}")
        return Response(
            json.dumps({'error': {'message': 'Failed to connect to ELITEA API'}}),
            status=502,
            content_type='application/json'
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return Response(
            json.dumps({'error': {'message': 'Internal server error'}}),
            status=500,
            content_type='application/json'
        )

@app.route('/v1/messages/count_tokens', methods=['POST'])
def count_tokens():
    """Handle token counting requests - use local estimation"""

    try:
        body = request.get_json()
        if not body:
            logger.warning("Token count request with no JSON body")
            return Response(
                json.dumps({'error': {'message': 'Request body must be valid JSON'}}),
                status=400,
                content_type='application/json'
            )

        # Token estimation based on character count
        text = ""
        if 'messages' in body:
            for msg in body['messages']:
                if isinstance(msg.get('content'), str):
                    text += msg['content']
                elif isinstance(msg.get('content'), list):
                    for item in msg['content']:
                        if item.get('type') == 'text':
                            text += item.get('text', '')

        estimated_tokens = max(1, len(text) // config.TOKEN_ESTIMATION_RATIO)
        logger.info(f"Estimated tokens: {estimated_tokens} (from {len(text)} chars)")

        return Response(
            json.dumps({'input_tokens': estimated_tokens}),
            status=200,
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"Token counting error: {e}")
        return Response(
            json.dumps({'error': {'message': 'Token counting failed'}}),
            status=500,
            content_type='application/json'
        )

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint with ELITEA connectivity test"""
    health_data = {
        'status': 'ok',
        'elitea_base_url': config.ELITEA_BASE_URL,
        'server_port': config.SERVER_PORT
    }

    try:
        # Test ELITEA API connectivity
        response = requests.get(
            f"{config.ELITEA_BASE_URL.rstrip('/v1')}/health",
            headers=config.get_elitea_headers(),
            timeout=5
        )
        if response.status_code == 200:
            health_data['elitea_status'] = 'connected'
        else:
            health_data['elitea_status'] = f'error_{response.status_code}'
    except requests.exceptions.RequestException:
        health_data['elitea_status'] = 'connection_failed'
    except Exception as e:
        logger.warning(f"Health check error: {e}")
        health_data['elitea_status'] = 'unknown'

    status_code = 200 if health_data.get('elitea_status') == 'connected' else 503
    return Response(
        json.dumps(health_data),
        status=status_code,
        content_type='application/json'
    )

def display_startup_banner():
    """Display colorful ASCII art banner on startup."""
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}
 ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
██║     ██║     ███████║██║   ██║██║  ██║█████╗
██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
{Style.RESET_ALL}
{Fore.MAGENTA}{Style.BRIGHT}
███████╗██╗     ██╗████████╗███████╗ █████╗
██╔════╝██║     ██║╚══██╔══╝██╔════╝██╔══██╗
█████╗  ██║     ██║   ██║   █████╗  ███████║
██╔══╝  ██║     ██║   ██║   ██╔══╝  ██╔══██║
███████╗███████╗██║   ██║   ███████╗██║  ██║
╚══════╝╚══════╝╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{Style.RESET_ALL}
{Fore.YELLOW}{Style.BRIGHT}
██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝
██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝
██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝
{Style.RESET_ALL}
{Fore.GREEN}┌─────────────────────────────────────────────────┐
│  {Fore.BLUE}{Style.BRIGHT}Secure proxy bridging Claude Code ↔ ELITEA{Style.RESET_ALL}{Fore.GREEN}     │
│ {Fore.BLUE}Model mapping • Parameter filtering • Stream{Style.RESET_ALL}{Fore.GREEN}    │
└─────────────────────────────────────────────────┘{Style.RESET_ALL}
"""

    # Print the banner
    print(banner)

if __name__ == '__main__':
    try:
        # Display startup banner
        display_startup_banner()

        # Validate configuration on startup
        logger.info(f"Starting ELITEA proxy server on http://{config.SERVER_HOST}:{config.SERVER_PORT}")
        logger.info(f"Forwarding requests to: {config.ELITEA_BASE_URL}")
        logger.info(f"Configuration: {config}")

        # Start the Flask application
        app.run(
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            debug=config.SERVER_DEBUG
        )

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set the required environment variables. See .env.example for reference.")
        exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        exit(1)
