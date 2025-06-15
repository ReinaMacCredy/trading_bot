#!/usr/bin/env python3
"""
Trading Bot Web Server
Entry point for running the FastAPI application with SSL support
"""

import argparse
import uvicorn
import logging
from pathlib import Path
import ssl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Trading Bot Web Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to"
    )
    parser.add_argument(
        "--ssl-cert",
        help="Path to SSL certificate file"
    )
    parser.add_argument(
        "--ssl-key",
        help="Path to SSL key file"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    return parser.parse_args()

def validate_ssl_config(args):
    """Validate SSL configuration"""
    if args.ssl_cert or args.ssl_key:
        if not (args.ssl_cert and args.ssl_key):
            raise ValueError("Both SSL certificate and key must be provided")
        
        cert_path = Path(args.ssl_cert)
        key_path = Path(args.ssl_key)
        
        if not cert_path.exists():
            raise FileNotFoundError(f"SSL certificate not found: {args.ssl_cert}")
        if not key_path.exists():
            raise FileNotFoundError(f"SSL key not found: {args.ssl_key}")
            
        return True
    return False

def main():
    """Main entry point"""
    args = parse_args()
    
    # Configure server settings
    server_config = {
        "app": "src.web.server:app",
        "host": args.host,
        "port": args.port,
        "reload": args.debug,
        "workers": 1,  # Single worker for MT5 client
        "log_level": "debug" if args.debug else "info"
    }
    
    # Configure SSL if enabled
    if validate_ssl_config(args):
        logger.info("SSL enabled")
        server_config.update({
            "ssl_keyfile": args.ssl_key,
            "ssl_certfile": args.ssl_cert
        })
    
    # Start server
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"SSL enabled: {validate_ssl_config(args)}")
    logger.info(f"Debug mode: {args.debug}")
    
    uvicorn.run(**server_config)

if __name__ == "__main__":
    main() 