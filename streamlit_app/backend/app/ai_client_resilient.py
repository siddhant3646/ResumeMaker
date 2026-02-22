"""
Resilient AI Client with Fallbacks, Retries, and Circuit Breaker Pattern
"""

import asyncio
import aiohttp
import time
import logging
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class CircuitBreaker:
    """Circuit breaker for provider health tracking"""
    failures: int = 0
    last_failure: Optional[float] = None
    status: ProviderStatus = ProviderStatus.HEALTHY
    
    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= 3:
            self.status = ProviderStatus.UNAVAILABLE
    
    def record_success(self):
        self.failures = max(0, self.failures - 1)
        if self.failures == 0:
            self.status = ProviderStatus.HEALTHY
            self.last_failure = None
    
    def is_open(self, timeout: int = 300) -> bool:
        """Check if circuit is open (unavailable)"""
        if self.status != ProviderStatus.UNAVAILABLE:
            return False
        
        # Auto-close after timeout
        if self.last_failure and (time.time() - self.last_failure) > timeout:
            self.status = ProviderStatus.DEGRADED
            self.failures = 2  # Keep some failure count
            return False
        
        return True


@dataclass
class AIProvider:
    """AI provider configuration"""
    name: str
    model: str
    timeout: int
    priority: int
    max_tokens: int = 4096
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)


class ResilientAIClient:
    """
    AI client with:
    - Multiple provider fallbacks
    - Exponential backoff retries
    - Circuit breaker pattern
    - Request timeouts
    - Health monitoring
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Provider configurations with fallbacks
        self.providers = [
            AIProvider(
                name="mistral-large",
                model="mistralai/mistral-large-3-675b-instruct-2512",
                timeout=90,
                priority=1,
                max_tokens=4096
            ),
            AIProvider(
                name="kimi-k2",
                model="moonshotai/kimi-k2.5",
                timeout=60,
                priority=2,
                max_tokens=4096
            ),
            AIProvider(
                name="stepfun-flash",
                model="stepfun-ai/step-3.5-flash",
                timeout=60,
                priority=3,
                max_tokens=4096
            ),
            AIProvider(
                name="qwen-2-5",
                model="qwen/qwen2.5-7b-instruct",
                timeout=60,
                priority=4,
                max_tokens=4096
            )
        ]
        
        # Sort by priority
        self.providers.sort(key=lambda p: p.priority)
        
        # Request tracking
        self.request_count = 0
        self.failure_count = 0
        
        logger.info(f"ResilientAIClient initialized with {len(self.providers)} providers")
    
    def _get_available_providers(self) -> List[AIProvider]:
        """Get list of healthy providers, sorted by priority"""
        available = []
        for provider in self.providers:
            if not provider.circuit_breaker.is_open():
                available.append(provider)
        
        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda p: p.priority)
        return available
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def _call_provider_with_retry(
        self,
        provider: AIProvider,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call a specific provider with retry logic"""
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": provider.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": min(max_tokens, provider.max_tokens),
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=provider.timeout)
                ) as response:
                    
                    if response.status == 429:
                        # Rate limited - retry after delay
                        retry_after = int(response.headers.get('Retry-After', 5))
                        logger.warning(f"Rate limited by {provider.name}, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        raise aiohttp.ClientError(f"Rate limited: {response.status}")
                    
                    response.raise_for_status()
                    
                    data = await response.json()
                    
                    # Validate response structure
                    if "choices" not in data or not data["choices"]:
                        raise ValueError(f"Invalid response from {provider.name}: missing choices")
                    
                    content = data["choices"][0]["message"]["content"]
                    
                    # Record success
                    provider.circuit_breaker.record_success()
                    
                    return content
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout calling {provider.name}")
                provider.circuit_breaker.record_failure()
                raise
                
            except aiohttp.ClientError as e:
                logger.warning(f"Client error calling {provider.name}: {e}")
                provider.circuit_breaker.record_failure()
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error calling {provider.name}: {e}")
                provider.circuit_breaker.record_failure()
                raise
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.15,
        max_tokens: int = 4096,
        fallback_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Generate content with automatic provider fallback
        
        Args:
            prompt: The prompt to send
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            fallback_callback: Optional callback when falling back to different provider
            
        Returns:
            Generated text
            
        Raises:
            Exception: If all providers fail
        """
        if not self.api_key:
            raise ValueError("API key not configured")
        
        self.request_count += 1
        
        available_providers = self._get_available_providers()
        
        if not available_providers:
            # All circuits are open - try resetting after timeout
            logger.warning("All provider circuits open, attempting reset")
            await asyncio.sleep(5)
            available_providers = self._get_available_providers()
            
            if not available_providers:
                raise Exception("All AI providers unavailable")
        
        last_error = None
        attempted_providers = []
        
        for provider in available_providers:
            attempted_providers.append(provider.name)
            
            try:
                logger.info(f"Attempting generation with {provider.name}")
                
                result = await self._call_provider_with_retry(
                    provider,
                    prompt,
                    temperature,
                    max_tokens
                )
                
                logger.info(f"Successfully generated with {provider.name}")
                
                # Notify about fallback if used
                if fallback_callback and provider != available_providers[0]:
                    fallback_callback(f"Fell back to {provider.name}")
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue
        
        # All providers failed
        self.failure_count += 1
        error_msg = f"All providers failed after attempting: {', '.join(attempted_providers)}"
        logger.error(error_msg)
        raise Exception(f"{error_msg}. Last error: {last_error}")
    
    async def generate_batch(
        self,
        prompts: List[str],
        temperature: float = 0.15,
        max_tokens: int = 4096,
        max_concurrency: int = 3
    ) -> List[str]:
        """
        Generate multiple responses with concurrency limiting
        
        Args:
            prompts: List of prompts to process
            temperature: Temperature for generation
            max_tokens: Maximum tokens per generation
            max_concurrency: Maximum concurrent requests
            
        Returns:
            List of generated texts (may contain None for failed requests)
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def generate_with_semaphore(prompt: str) -> Optional[str]:
            async with semaphore:
                try:
                    return await self.generate(prompt, temperature, max_tokens)
                except Exception as e:
                    logger.error(f"Batch generation failed for prompt: {e}")
                    return None
        
        tasks = [generate_with_semaphore(p) for p in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        return [r if not isinstance(r, Exception) else None for r in results]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return {
            "providers": [
                {
                    "name": p.name,
                    "status": p.circuit_breaker.status.value,
                    "failures": p.circuit_breaker.failures,
                    "priority": p.priority
                }
                for p in self.providers
            ],
            "total_requests": self.request_count,
            "failed_requests": self.failure_count,
            "success_rate": (
                (self.request_count - self.failure_count) / max(1, self.request_count) * 100
            )
        }
    
    async def health_check(self) -> bool:
        """Quick health check - returns True if any provider is available"""
        available = self._get_available_providers()
        return len(available) > 0
