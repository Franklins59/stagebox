"""
Stagebox Job Queue

Simple in-memory job queue for tracking stage execution progress.
"""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class JobQueue:
    """Simple in-memory job queue for tracking stage execution progress."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def create_job(self, stage: str, total: int) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())[:8]
        with self._lock:
            self.jobs[job_id] = {
                'stage': stage,
                'status': 'running',
                'current': 0,
                'total': total,
                'current_device': None,
                'results': [],
                'created_at': time.time(),
            }
        return job_id
    
    def update_job(self, job_id: str, current: int = None, 
                   current_device: str = None, result: dict = None):
        """Update job progress."""
        with self._lock:
            if job_id not in self.jobs:
                return
            job = self.jobs[job_id]
            if current is not None:
                job['current'] = current
            if current_device is not None:
                job['current_device'] = current_device
            if result is not None:
                job['results'].append(result)
    
    def complete_job(self, job_id: str, result_data: Dict = None, status: str = 'completed'):
        """Mark job as completed with optional result data."""
        with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id]['status'] = status
                self.jobs[job_id]['current_device'] = None
                if result_data:
                    self.jobs[job_id]['result_data'] = result_data
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status."""
        with self._lock:
            return self.jobs.get(job_id, {}).copy()
    
    def cleanup_old_jobs(self, max_age_seconds: int = 300):
        """Remove jobs older than max_age_seconds."""
        now = time.time()
        with self._lock:
            to_remove = [
                jid for jid, job in self.jobs.items()
                if now - job['created_at'] > max_age_seconds
            ]
            for jid in to_remove:
                del self.jobs[jid]


# Global job queue instance
job_queue = JobQueue()


def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    return job_queue
