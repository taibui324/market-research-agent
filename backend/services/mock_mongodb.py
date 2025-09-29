"""
Mock MongoDB service for development when MongoDB is not available.
Stores data in memory for testing and development purposes.
"""

from datetime import datetime
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MockMongoDBService:
    """Mock MongoDB service that stores data in memory."""
    
    def __init__(self, uri: str = None):
        logger.info("Using MockMongoDBService - data will be stored in memory only")
        self._jobs = {}
        self._reports = {}
    
    def _convert_objectid_to_str(self, obj: Any) -> Any:
        """Mock implementation - just return the object as-is."""
        return obj

    def create_job(self, job_id: str, inputs: Dict[str, Any]) -> None:
        """Create a new research job record in memory."""
        self._jobs[job_id] = {
            "job_id": job_id,
            "inputs": inputs,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        logger.info(f"Created job {job_id} in memory")

    def update_job(self, job_id: str, 
                  status: str = None,
                  result: Dict[str, Any] = None,
                  error: str = None,
                  metadata: Dict[str, Any] = None) -> None:
        """Update an existing research job record."""
        if job_id not in self._jobs:
            logger.warning(f"Job {job_id} not found in memory, creating new entry")
            self._jobs[job_id] = {
                "job_id": job_id,
                "inputs": {},
                "created_at": datetime.utcnow()
            }
        
        update_data = {"updated_at": datetime.utcnow()}
        
        if status:
            update_data["status"] = status
        if result:
            update_data["result"] = result
        if error:
            update_data["error"] = error
        if metadata:
            update_data["metadata"] = metadata
            
        self._jobs[job_id].update(update_data)
        logger.info(f"Updated job {job_id} with status: {status}")

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a research job by ID."""
        job = self._jobs.get(job_id)
        if job:
            logger.info(f"Retrieved job {job_id} from memory")
        else:
            logger.warning(f"Job {job_id} not found in memory")
        return job

    def delete_job(self, job_id: str) -> bool:
        """Delete a research job by ID."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.info(f"Deleted job {job_id} from memory")
            return True
        else:
            logger.warning(f"Job {job_id} not found for deletion")
            return False

    def list_jobs(self, limit: int = 100, status: str = None) -> list:
        """List research jobs with optional filtering."""
        jobs = list(self._jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.get("status") == status]
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        
        return jobs[:limit]

    def save_report(self, job_id: str, report_content: str, 
                   report_type: str = "3c_analysis", metadata: Dict[str, Any] = None) -> str:
        """Save a research report."""
        report_id = f"report_{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        self._reports[report_id] = {
            "report_id": report_id,
            "job_id": job_id,
            "content": report_content,
            "type": report_type,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        
        logger.info(f"Saved report {report_id} for job {job_id} in memory")
        return report_id

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a research report by ID."""
        report = self._reports.get(report_id)
        if report:
            logger.info(f"Retrieved report {report_id} from memory")
        else:
            logger.warning(f"Report {report_id} not found in memory")
        return report

    def get_reports_by_job(self, job_id: str) -> list:
        """Get all reports for a specific job."""
        reports = [
            report for report in self._reports.values() 
            if report.get("job_id") == job_id
        ]
        logger.info(f"Found {len(reports)} reports for job {job_id}")
        return reports

    def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up old jobs (mock implementation)."""
        # In a real implementation, this would delete jobs older than X days
        # For the mock, we'll just log and return 0
        logger.info(f"Mock cleanup: would remove jobs older than {days} days")
        return 0

    def health_check(self) -> bool:
        """Check if the service is healthy."""
        return True  # Mock service is always healthy

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "total_jobs": len(self._jobs),
            "total_reports": len(self._reports),
            "service_type": "mock",
            "memory_storage": True,
            "jobs_by_status": {
                status: len([j for j in self._jobs.values() if j.get("status") == status])
                for status in ["pending", "processing", "completed", "failed"]
            }
        }
