# middleware.py

import time
import redis
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

# Initialize a Redis connection
redis_client = redis.StrictRedis.from_url(settings.CACHES['default']['LOCATION'])

class RedisActionTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user actions and store metrics in Redis.
    """

    def process_request(self, request):
        """
        This function triggers on each request and logs the action in Redis.
        """
        request.start_time = time.time()  # To calculate the latency later

    def process_response(self, request, response):
        """
        This function triggers after a response is processed.
        """
        # Calculate request latency
        latency = time.time() - request.start_time

        # Identify user or anonymous actions
        user_type = 'anonymous' if isinstance(request.user, AnonymousUser) else request.user.user_type  # Assuming user has `user_type`
        
        # Get action metadata
        action = f"{request.method}_{request.path.strip('/')}"
        user_id = getattr(request.user, 'id', 'anonymous')  # Default to 'anonymous' for non-authenticated users

        # Increment Redis counters
        redis_client.hincrby(f"user:{user_id}:actions", action, 1)  # Tracks counts per action per user
        redis_client.expire(f"user:{user_id}:actions", 3600)  # 1-hour expiration on action counts

        # Track global action counts with TTL
        redis_client.hincrby("global:actions", action, 1)
        redis_client.expire("global:actions", 3600)

        # Store latency if needed for analysis
        redis_client.rpush(f"user:{user_id}:latency", latency)  # Track latencies
        redis_client.expire(f"user:{user_id}:latency", 3600)

        return response
