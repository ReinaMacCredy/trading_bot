"""
Security and Authentication Module
Handles webhook verification, rate limiting, and API authentication
"""
import hmac
import hashlib
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis
import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class WebhookSecurity:
    """Webhook signature verification and security"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key
        
    def verify_signature(self, request_body: bytes, signature: str) -> bool:
        """Verify TradingView webhook signature"""
        if not self.secret_key:
            # If no secret key configured, allow all (development mode)
            logger.warning("Webhook signature verification disabled - no secret key configured")
            return True
        
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # Clean signature (remove prefix if present)
            if signature.startswith("sha256="):
                signature = signature[7:]
            
            # Compare signatures using constant-time comparison
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def generate_test_signature(self, request_body: bytes) -> str:
        """Generate signature for testing purposes"""
        if not self.secret_key:
            return "test_signature"
        
        signature = hmac.new(
            self.secret_key.encode(),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"

class RateLimiter:
    """Rate limiting for API endpoints and webhooks"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    async def check_rate_limit(self, identifier: str, limit: int, window: int = 60) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            True if within limit, False if exceeded
        """
        try:
            key = f"rate_limit:{identifier}"
            current_time = int(time.time())
            window_start = current_time - window
            
            # Remove old entries
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = await self.redis.zcard(key)
            
            if current_count >= limit:
                return False
            
            # Add current request
            await self.redis.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            await self.redis.expire(key, window)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # On error, allow request (fail open)
            return True
    
    async def get_rate_limit_info(self, identifier: str, window: int = 60) -> Dict[str, Any]:
        """Get current rate limit information"""
        try:
            key = f"rate_limit:{identifier}"
            current_time = int(time.time())
            window_start = current_time - window
            
            # Remove old entries
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Get current count and remaining time
            current_count = await self.redis.zcard(key)
            ttl = await self.redis.ttl(key)
            
            return {
                "current_requests": current_count,
                "window_remaining": max(0, ttl),
                "timestamp": current_time
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {
                "current_requests": 0,
                "window_remaining": window,
                "timestamp": int(time.time())
            }

class JWTAuth:
    """JWT token authentication for API endpoints"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

class APIKeyAuth:
    """API key authentication for external integrations"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user information"""
        try:
            key = f"api_key:{api_key}"
            user_data = await self.redis.hgetall(key)
            
            if not user_data:
                return None
            
            # Update last used timestamp
            await self.redis.hset(key, "last_used", datetime.utcnow().isoformat())
            
            return {
                "user_id": user_data.get("user_id"),
                "permissions": user_data.get("permissions", "").split(","),
                "created_at": user_data.get("created_at"),
                "last_used": user_data.get("last_used")
            }
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    async def create_api_key(self, user_id: str, permissions: list) -> str:
        """Create new API key for user"""
        import secrets
        
        api_key = f"tk_{secrets.token_urlsafe(32)}"
        
        key_data = {
            "user_id": user_id,
            "permissions": ",".join(permissions),
            "created_at": datetime.utcnow().isoformat(),
            "last_used": ""
        }
        
        await self.redis.hset(f"api_key:{api_key}", mapping=key_data)
        
        return api_key
    
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key"""
        try:
            result = await self.redis.delete(f"api_key:{api_key}")
            return result > 0
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            return False

# Security dependencies for FastAPI
security = HTTPBearer(auto_error=False)

async def verify_webhook_signature(request: Request, webhook_security: WebhookSecurity) -> bool:
    """FastAPI dependency for webhook signature verification"""
    signature = request.headers.get("X-TradingView-Signature")
    if not signature:
        signature = request.headers.get("X-Webhook-Signature")
    
    if not signature:
        if webhook_security.secret_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )
        return True
    
    # Get request body
    body = await request.body()
    
    if not webhook_security.verify_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    return True

async def check_api_rate_limit(request: Request, rate_limiter: RateLimiter, 
                              limit: int = 100) -> bool:
    """FastAPI dependency for API rate limiting"""
    # Use IP address as identifier
    client_ip = request.client.host
    identifier = f"api:{client_ip}"
    
    if not await rate_limiter.check_rate_limit(identifier, limit):
        # Get rate limit info for headers
        info = await rate_limiter.get_rate_limit_info(identifier)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(max(0, limit - info["current_requests"])),
                "X-RateLimit-Reset": str(info["window_remaining"]),
                "Retry-After": str(info["window_remaining"])
            }
        )
    
    return True

async def verify_api_token(credentials: HTTPAuthorizationCredentials, 
                          jwt_auth: JWTAuth) -> Dict[str, Any]:
    """FastAPI dependency for JWT token verification"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )
    
    payload = jwt_auth.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload

async def verify_api_key(request: Request, api_key_auth: APIKeyAuth) -> Dict[str, Any]:
    """FastAPI dependency for API key verification"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
    
    user_data = await api_key_auth.validate_api_key(api_key)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user_data

# Utility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_client_ip(request: Request) -> str:
    """Get client IP address with proxy support"""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host

class SecurityMiddleware:
    """Security middleware for additional protection"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add security headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Security headers
                    security_headers = {
                        b"x-content-type-options": b"nosniff",
                        b"x-frame-options": b"DENY",
                        b"x-xss-protection": b"1; mode=block",
                        b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                        b"content-security-policy": b"default-src 'self'",
                        b"referrer-policy": b"strict-origin-when-cross-origin"
                    }
                    
                    headers.update(security_headers)
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send) 