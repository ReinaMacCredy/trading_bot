#!/usr/bin/env python3
"""
HTTPS Trading Server Entry Point
Standalone server for TradingView webhooks and web trading
"""
import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.web.main import run_server
from src.config.config_loader import ConfigLoader

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/web_server.log', encoding='utf-8')
        ]
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Trading HTTPS Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--ssl-cert', help='SSL certificate file path')
    parser.add_argument('--ssl-key', help='SSL private key file path')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    logger.info("🚀 Starting Trading HTTPS Server")
    logger.info(f"📍 Server will bind to {args.host}:{args.port}")
    
    if args.ssl_cert and args.ssl_key:
        logger.info("🔒 SSL enabled")
    else:
        logger.info("🌐 Running in HTTP mode (SSL disabled)")
    
    try:
        # Load configuration
        if args.config:
            os.environ['CONFIG_PATH'] = args.config
        
        # Run server
        run_server(
            host=args.host,
            port=args.port,
            ssl_certfile=args.ssl_cert,
            ssl_keyfile=args.ssl_key
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 