import time
import logging
import functools
from enum import Enum

logger = logging.getLogger('circuit_breaker')

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"       # Normal operation, requests flow through
    OPEN = "OPEN"           # Circuit is open, requests fail fast
    HALF_OPEN = "HALF_OPEN" # Testing if the circuit can be closed again

class CircuitBreaker:
    """
    Implementation of the Circuit Breaker pattern to prevent cascade failures
    """
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        """
        Initialize a circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time to wait before trying to close the circuit (seconds)
        """
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        logger.debug(f"Circuit breaker initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def record_failure(self):
        """Record a failure and possibly open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    def record_success(self):
        """Record a success and possibly close the circuit"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self._close_circuit()
    
    def allow_request(self):
        """Check if a request is allowed to proceed"""
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self._half_open_circuit()
                return True
            return False
            
        # HALF_OPEN state - allow one request to test the waters
        return True
    
    def _open_circuit(self):
        """Open the circuit to prevent further requests"""
        if self.state != CircuitState.OPEN:
            logger.warning(f"Opening circuit after {self.failure_count} failures")
            self.state = CircuitState.OPEN
    
    def _half_open_circuit(self):
        """Set circuit to half-open to test if service is recovered"""
        logger.info(f"Setting circuit to half-open after {self.recovery_timeout}s timeout")
        self.state = CircuitState.HALF_OPEN
    
    def _close_circuit(self):
        """Close the circuit to resume normal operation"""
        logger.info("Closing circuit after successful request")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
    
    def __str__(self):
        return f"CircuitBreaker(state={self.state.value}, failures={self.failure_count}/{self.failure_threshold})"


def circuit_breaker(cb=None, failure_threshold=5, recovery_timeout=60):
    """
    Decorator to apply circuit breaker pattern to a function
    
    Args:
        cb: Circuit breaker instance to use, or None to create a new one
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time to wait before trying to close the circuit (seconds)
    """
    if cb is None:
        cb = CircuitBreaker(failure_threshold, recovery_timeout)
        
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not cb.allow_request():
                logger.warning(f"Circuit is open, fast-failing request to {func.__name__}")
                raise CircuitOpenError(f"Circuit breaker is open for {func.__name__}")
                
            try:
                result = func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
                
        return wrapper
        
    return decorator


class CircuitOpenError(Exception):
    """Exception raised when a circuit is open"""
    pass 