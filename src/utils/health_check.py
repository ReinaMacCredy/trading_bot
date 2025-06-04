"""
Health Check Module for Professional Discord Trading Bot

Provides health monitoring endpoints and system status checks for production deployment.
"""

import os
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class HealthChecker:
    """
    Health check system for monitoring bot status in production
    """
    
    def __init__(self, bot=None, config=None):
        self.bot = bot
        self.config = config
        self.start_time = time.time()
        self.health_file = Path("/tmp/bot_healthy")
        self.last_check = time.time()
        
    async def check_discord_connection(self) -> Dict[str, Any]:
        """Check Discord connection status"""
        try:
            if self.bot and hasattr(self.bot, 'is_ready'):
                is_ready = self.bot.is_ready()
                is_closed = self.bot.is_closed()
                
                return {
                    "status": "healthy" if is_ready and not is_closed else "unhealthy",
                    "ready": is_ready,
                    "closed": is_closed,
                    "latency": round(self.bot.latency * 1000, 2) if is_ready else None,
                    "guild_count": len(self.bot.guilds) if is_ready else 0
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Bot instance not available"
                }
        except Exception as e:
            logger.error(f"Error checking Discord connection: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_database_connection(self) -> Dict[str, Any]:
        """Check database connection status"""
        try:
            # This would be implemented based on your database setup
            # For now, we'll check if the database URL is configured
            db_url = os.getenv('DATABASE_URL')
            if db_url:
                return {
                    "status": "configured",
                    "type": "postgresql" if "postgresql" in db_url else "unknown"
                }
            else:
                return {
                    "status": "not_configured",
                    "message": "Database URL not set"
                }
        except Exception as e:
            logger.error(f"Error checking database connection: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_exchange_connection(self) -> Dict[str, Any]:
        """Check exchange API connection status"""
        try:
            # Check if API keys are configured
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_SECRET')
            
            if api_key and api_secret:
                return {
                    "status": "configured",
                    "sandbox": os.getenv('EXCHANGE_SANDBOX', 'true').lower() == 'true'
                }
            else:
                return {
                    "status": "not_configured",
                    "message": "Exchange API credentials not set"
                }
        except Exception as e:
            logger.error(f"Error checking exchange connection: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                "status": "healthy",
                "memory": {
                    "used_percent": memory.percent,
                    "available_mb": round(memory.available / 1024 / 1024, 2),
                    "total_mb": round(memory.total / 1024 / 1024, 2)
                },
                "disk": {
                    "used_percent": disk.percent,
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2)
                },
                "cpu_percent": cpu_percent
            }
        except ImportError:
            return {
                "status": "unavailable",
                "message": "psutil not installed"
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        try:
            # Run all health checks
            discord_health = await self.check_discord_connection()
            database_health = await self.check_database_connection()
            exchange_health = await self.check_exchange_connection()
            system_health = await self.check_system_resources()
            
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            uptime_minutes = round(uptime_seconds / 60, 2)
            uptime_hours = round(uptime_seconds / 3600, 2)
            
            # Determine overall status
            overall_status = "healthy"
            if discord_health["status"] == "unhealthy":
                overall_status = "unhealthy"
            elif any(health.get("status") == "error" for health in [database_health, exchange_health, system_health]):
                overall_status = "degraded"
            
            health_data = {
                "overall_status": overall_status,
                "timestamp": time.time(),
                "uptime": {
                    "seconds": round(uptime_seconds, 2),
                    "minutes": uptime_minutes,
                    "hours": uptime_hours
                },
                "components": {
                    "discord": discord_health,
                    "database": database_health,
                    "exchange": exchange_health,
                    "system": system_health
                },
                "environment": os.getenv('ENVIRONMENT', 'unknown'),
                "version": "1.0.0"  # This could be read from a version file
            }
            
            # Update health file for Docker health checks
            await self.update_health_file(overall_status == "healthy")
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error in comprehensive health check: {e}")
            await self.update_health_file(False)
            return {
                "overall_status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
    
    async def update_health_file(self, is_healthy: bool):
        """Update health file for Docker health checks"""
        try:
            if is_healthy:
                self.health_file.touch()
                self.last_check = time.time()
            else:
                if self.health_file.exists():
                    self.health_file.unlink()
        except Exception as e:
            logger.error(f"Error updating health file: {e}")
    
    async def start_health_monitor(self, interval: int = 30):
        """Start periodic health monitoring"""
        logger.info(f"Starting health monitor with {interval}s interval")
        
        while True:
            try:
                health_data = await self.get_comprehensive_health()
                
                # Log health status periodically
                if time.time() - self.last_check > 300:  # Every 5 minutes
                    logger.info(f"Health check: {health_data['overall_status']}")
                    self.last_check = time.time()
                
                # Save health data to file for external monitoring
                health_file_path = Path("logs/health.json")
                health_file_path.parent.mkdir(exist_ok=True)
                
                with open(health_file_path, 'w') as f:
                    json.dump(health_data, f, indent=2)
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Health monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(interval)

# Convenience functions for FastAPI or Flask integration
async def health_check_endpoint():
    """Health check endpoint for web frameworks"""
    health_checker = HealthChecker()
    health_data = await health_checker.get_comprehensive_health()
    
    # Return appropriate HTTP status code
    status_code = 200 if health_data["overall_status"] == "healthy" else 503
    
    return health_data, status_code

def simple_health_check() -> bool:
    """Simple synchronous health check for Docker"""
    health_file = Path("/tmp/bot_healthy")
    return health_file.exists()

# CLI function for manual health checks
async def main():
    """CLI health check function"""
    health_checker = HealthChecker()
    health_data = await health_checker.get_comprehensive_health()
    
    print(json.dumps(health_data, indent=2))
    
    # Exit with appropriate code
    exit_code = 0 if health_data["overall_status"] == "healthy" else 1
    exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main()) 