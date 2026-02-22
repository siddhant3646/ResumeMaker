"""
Queue Manager - Redis-based job queue for handling 5000 concurrent users
Uses Redis Streams for reliable job processing
"""

import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum


class JobStatus(Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ResumeJob:
    """Represents a resume generation job"""
    job_id: str
    user_id: str
    status: str
    created_at: float
    updated_at: float
    resume_data: Dict[str, Any]
    job_description: Optional[str]
    config: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    queue_position: int = 0
    estimated_wait_seconds: int = 0


class QueueManager:
    """
    Manages resume generation jobs using Redis Streams
    Handles queueing, status tracking, and result retrieval
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize queue manager
        
        Args:
            redis_client: Redis client instance (optional, for testing without Redis)
        """
        self.redis = redis_client
        self.stream_key = "resume_jobs"
        self.consumer_group = "resume_workers"
        self.jobs_key = "resume_job_data"
        self.enabled = redis_client is not None
        
        if self.enabled:
            self._create_consumer_group()
    
    def _create_consumer_group(self):
        """Create consumer group if it doesn't exist"""
        try:
            self.redis.xgroup_create(
                self.stream_key,
                self.consumer_group,
                id='0',
                mkstream=True
            )
        except Exception as e:
            # Group may already exist
            pass
    
    def submit_job(
        self,
        user_id: str,
        resume_data: Dict[str, Any],
        job_description: Optional[str],
        config: Dict[str, Any]
    ) -> ResumeJob:
        """
        Submit a new resume generation job
        
        Args:
            user_id: User's unique identifier
            resume_data: Parsed resume data
            job_description: Job description text (optional for ATS-only mode)
            config: Generation configuration
            
        Returns:
            ResumeJob: Created job with ID and queue position
        """
        job_id = str(uuid.uuid4())
        timestamp = time.time()
        
        job = ResumeJob(
            job_id=job_id,
            user_id=user_id,
            status=JobStatus.PENDING.value,
            created_at=timestamp,
            updated_at=timestamp,
            resume_data=resume_data,
            job_description=job_description,
            config=config
        )
        
        if self.enabled:
            # Store job data in Redis hash
            job_key = f"{self.jobs_key}:{job_id}"
            self.redis.hset(job_key, mapping={
                "data": json.dumps(asdict(job)),
                "created_at": timestamp
            })
            self.redis.expire(job_key, 86400)  # 24 hour TTL
            
            # Add to stream for processing
            self.redis.xadd(
                self.stream_key,
                {"job_id": job_id},
                id='*'
            )
            
            # Calculate queue position
            job.queue_position = self._get_queue_position(job_id)
            job.estimated_wait_seconds = job.queue_position * 5  # ~5 seconds per job
        else:
            # No Redis - process immediately (single user mode)
            job.queue_position = 0
            job.estimated_wait_seconds = 0
        
        return job
    
    def _get_queue_position(self, job_id: str) -> int:
        """Get position in queue"""
        if not self.enabled:
            return 0
        
        try:
            # Get all pending jobs from stream
            jobs = self.redis.xrange(self.stream_key)
            
            position = 0
            for _, fields in jobs:
                if fields.get(b"job_id", b"").decode() == job_id:
                    break
                position += 1
            
            return position
        except:
            return 0
    
    def get_job_status(self, job_id: str) -> Optional[ResumeJob]:
        """Get current status of a job"""
        if not self.enabled:
            return None
        
        try:
            job_key = f"{self.jobs_key}:{job_id}"
            data = self.redis.hget(job_key, "data")
            
            if data:
                job_dict = json.loads(data)
                return ResumeJob(**job_dict)
            
            return None
        except Exception as e:
            print(f"Error getting job status: {e}")
            return None
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update job status and result"""
        if not self.enabled:
            return
        
        try:
            job_key = f"{self.jobs_key}:{job_id}"
            data = self.redis.hget(job_key, "data")
            
            if data:
                job_dict = json.loads(data)
                job_dict["status"] = status.value
                job_dict["updated_at"] = time.time()
                
                if result:
                    job_dict["result"] = result
                if error:
                    job_dict["error"] = error
                
                self.redis.hset(job_key, "data", json.dumps(job_dict))
        except Exception as e:
            print(f"Error updating job status: {e}")
    
    def get_next_job(self, consumer_name: str, block_ms: int = 5000) -> Optional[ResumeJob]:
        """
        Get next job from queue for processing
        
        Args:
            consumer_name: Name of the worker consumer
            block_ms: Milliseconds to block waiting for jobs
            
        Returns:
            ResumeJob or None if no jobs available
        """
        if not self.enabled:
            return None
        
        try:
            # Read from stream with consumer group
            messages = self.redis.xreadgroup(
                groupname=self.consumer_group,
                consumername=consumer_name,
                streams={self.stream_key: '>'},
                count=1,
                block=block_ms
            )
            
            if messages:
                stream_name, msgs = messages[0]
                msg_id, fields = msgs[0]
                job_id = fields.get(b"job_id", b"").decode()
                
                # Get full job data
                job = self.get_job_status(job_id)
                if job:
                    # Acknowledge message
                    self.redis.xack(self.stream_key, self.consumer_group, msg_id)
                    
                    # Update status to processing
                    self.update_job_status(job_id, JobStatus.PROCESSING)
                    job.status = JobStatus.PROCESSING.value
                    
                    return job
            
            return None
        except Exception as e:
            print(f"Error getting next job: {e}")
            return None
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up completed/failed jobs older than max_age_hours"""
        if not self.enabled:
            return
        
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            # Find and delete old jobs
            pattern = f"{self.jobs_key}:*"
            for key in self.redis.scan_iter(pattern):
                created_at = self.redis.hget(key, "created_at")
                if created_at and float(created_at) < cutoff_time:
                    self.redis.delete(key)
        except Exception as e:
            print(f"Error cleaning up jobs: {e}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            pending_jobs = len(self.redis.xrange(self.stream_key))
            
            # Count jobs by status
            status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
            
            pattern = f"{self.jobs_key}:*"
            for key in self.redis.scan_iter(pattern):
                data = self.redis.hget(key, "data")
                if data:
                    job_dict = json.loads(data)
                    status = job_dict.get("status", "unknown")
                    if status in status_counts:
                        status_counts[status] += 1
            
            return {
                "enabled": True,
                "pending_in_stream": pending_jobs,
                "total_tracked_jobs": sum(status_counts.values()),
                "by_status": status_counts
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


# Singleton instance
_queue_manager = None

def get_queue_manager(redis_client=None) -> QueueManager:
    """Get or create QueueManager singleton"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = QueueManager(redis_client)
    return _queue_manager
