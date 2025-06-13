# """
# HTTPS Trading Server
# Handles TradingView webhooks and web frontend orders
# """
# import asyncio
# import logging
# from contextlib import asynccontextmanager
# from typing import Dict, Any

# import uvicorn
# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import redis.asyncio as redis

# from .api.webhooks import webhook_router
# from .api.orders import orders_router
# from .api.status import status_router
# from .services.redis_service import RedisService
# from .services.order_matching import OrderMatchingService
# from .services.trading_service import TradingService
# from ..config.config_loader import ConfigLoader

# # Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Global services
# redis_service: RedisService = None
# order_matching: OrderMatchingService = None
# trading_service: TradingService = None

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan management"""
#     global redis_service, order_matching, trading_service
    
#     logger.info("🚀 Starting HTTPS Trading Server...")
    
#     try:
#         # Load configuration
#         config = ConfigLoader.load_config()
        
#         # Initialize Redis connection
#         redis_client = redis.Redis(
#             host=config.redis.host,
#             port=config.redis.port,
#             password=config.redis.password,
#             decode_responses=True
#         )
        
#         # Initialize services
#         redis_service = RedisService(redis_client)
#         trading_service = TradingService(config)
#         order_matching = OrderMatchingService(redis_service, trading_service)
        
#         # Test connections
#         await redis_service.test_connection()
#         await trading_service.initialize()
        
#         # Start background order matching
#         asyncio.create_task(order_matching.start_matching_loop())
        
#         logger.info("✅ All services initialized successfully")
#         yield
        
#     except Exception as e:
#         logger.error(f"❌ Failed to initialize services: {e}")
#         raise
#     finally:
#         # Cleanup
#         if redis_service:
#             await redis_service.close()
#         if trading_service:
#             await trading_service.close()
#         logger.info("🔹 Server shutdown complete")

# # Create FastAPI app
# app = FastAPI(
#     title="Trading HTTPS Server",
#     description="Receives TradingView signals and manages web trading orders",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # CORS middleware for web frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure appropriately for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])
# app.include_router(orders_router, prefix="/orders", tags=["orders"]) 
# app.include_router(status_router, prefix="/status", tags=["status"])

# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {
#         "status": "online",
#         "service": "Trading HTTPS Server",
#         "version": "1.0.0"
#     }

# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc):
#     """Global exception handler"""
#     logger.error(f"Unhandled exception: {exc}")
#     return JSONResponse(
#         status_code=500,
#         content={"error": "Internal server error"}
#     )

# def run_server(host: str = "0.0.0.0", port: int = 8000, ssl_certfile: str = None, ssl_keyfile: str = None):
#     """Run the HTTPS server"""
#     config = {
#         "app": "src.web.main:app",
#         "host": host,
#         "port": port,
#         "reload": False,
#         "access_log": True,
#         "log_level": "info"
#     }
    
#     # Add SSL configuration if certificates provided
#     if ssl_certfile and ssl_keyfile:
#         config.update({
#             "ssl_certfile": ssl_certfile,
#             "ssl_keyfile": ssl_keyfile
#         })
#         logger.info(f"🔒 Starting HTTPS server on {host}:{port}")
#     else:
#         logger.info(f"🌐 Starting HTTP server on {host}:{port}")
    
#     uvicorn.run(**config)

# if __name__ == "__main__":
#     run_server() 



from fastapi import FastAPI
from web.api import webhooks, orders

app = FastAPI(title="Trading System API")

app.include_router(webhooks.router, prefix="/api")
app.include_router(orders.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Trading system is running"}
