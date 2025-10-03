from datetime import datetime
from typing import Any, Dict, Optional

import certifi
from bson import ObjectId
from pymongo import MongoClient


class MongoDBService:
    def __init__(self, uri: str = None):
        if uri is None:
            # Use default MongoDB URI from environment
            import os
            uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        
        # Use certifi for SSL certificate verification with updated options
        self.client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            retryWrites=True,
            w='majority'
        )
        self.db = self.client.get_database('tavily_research')
        self.jobs = self.db.jobs
        self.reports = self.db.reports

    def _convert_objectid_to_str(self, obj: Any) -> Any:
        """Recursively convert ObjectId instances to strings in a document."""
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_objectid_to_str(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_objectid_to_str(item) for item in obj]
        else:
            return obj

    def create_job(self, job_id: str, inputs: Dict[str, Any]) -> None:
        """Create a new research job record."""
        self.jobs.insert_one({
            "job_id": job_id,
            "inputs": inputs,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

    def update_job(self, job_id: str, 
                  status: str = None,
                  result: Dict[str, Any] = None,
                  error: str = None,
                  metadata: Dict[str, Any] = None,
                  **kwargs) -> None:
        """Update a research job with results or status."""
        update_data = {"updated_at": datetime.utcnow()}
        
        if status:
            update_data["status"] = status
        if result:
            update_data["result"] = result
        if error:
            update_data["error"] = error
        if metadata:
            update_data["metadata"] = metadata
            
        # Handle any additional keyword arguments
        for key, value in kwargs.items():
            if value is not None:
                update_data[key] = value

        self.jobs.update_one(
            {"job_id": job_id},
            {"$set": update_data},
            upsert=True  # Create the job if it doesn't exist
        )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID."""
        job = self.jobs.find_one({"job_id": job_id})
        if job:
            return self._convert_objectid_to_str(job)
        return None



    def save_swot_analysis(self, job_id: str, swot_content: str, company: str = None) -> None:
        """Save SWOT analysis content to the database."""
        # Create a SWOT analysis document
        swot_doc = {
            "job_id": job_id,
            "company": company,
            "swot_content": swot_content,
            "created_at": datetime.utcnow()
        }
        
        # Insert into a dedicated SWOT collection
        if not hasattr(self, 'swot_analyses'):
            self.swot_analyses = self.db.swot_analyses
        
        self.swot_analyses.insert_one(swot_doc)
        
        # Also update the job record with SWOT completion status
        self.jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "swot_analysis_completed": True,
                "swot_analysis_company": company,
                "updated_at": datetime.utcnow()
            }}
        )

    def get_swot_analysis(self, job_id: str, company: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve SWOT analysis by job ID and optionally by company."""
        query = {"job_id": job_id}
        if company:
            query["company"] = company
            
        swot = self.swot_analyses.find_one(query)
        if swot:
            return self._convert_objectid_to_str(swot)
        return None

    def get_report(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a report by job ID."""
        report = self.reports.find_one({"job_id": job_id})
        if report:
            return self._convert_objectid_to_str(report)
        return None

    def store_report(self, job_id: str, report_data: Dict[str, Any] = None, **kwargs) -> None:
        """Store a research report with flexible data structure."""
        # Handle both old and new calling patterns
        if report_data:
            # New pattern: store_report(job_id, report_data={...})
            report_doc = {
                "job_id": job_id,
                "created_at": datetime.utcnow(),
                **report_data
            }
        else:
            # Legacy pattern: store_report(job_id, report_content="...", ...)
            report_doc = {
                "job_id": job_id,
                "created_at": datetime.utcnow(),
                **kwargs
            }
        
        # Upsert the report (update if exists, create if not)
        self.reports.update_one(
            {"job_id": job_id},
            {"$set": report_doc},
            upsert=True
        )

    def delete_job(self, job_id: str) -> bool:
        """Delete a research job by ID."""
        result = self.jobs.delete_one({"job_id": job_id})
        return result.deleted_count > 0

    def list_jobs(self, limit: int = 100, status: str = None) -> list:
        """List research jobs with optional filtering."""
        query = {}
        if status:
            query["status"] = status
        
        cursor = self.jobs.find(query).sort("created_at", -1).limit(limit)
        jobs = [self._convert_objectid_to_str(job) for job in cursor]
        return jobs

    def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up old jobs."""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = self.jobs.delete_many({
            "created_at": {"$lt": cutoff_date},
            "status": {"$in": ["completed", "failed"]}
        })
        return result.deleted_count

    def health_check(self) -> bool:
        """Check if the MongoDB service is healthy."""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        try:
            total_jobs = self.jobs.count_documents({})
            total_reports = self.reports.count_documents({})
            
            # Get job status distribution
            pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            status_counts = {doc["_id"]: doc["count"] for doc in self.jobs.aggregate(pipeline)}
            
            return {
                "total_jobs": total_jobs,
                "total_reports": total_reports,
                "service_type": "real",
                "database": self.db.name,
                "jobs_by_status": status_counts
            }
        except Exception as e:
            return {
                "error": str(e),
                "service_type": "real",
                "database": self.db.name
            } 