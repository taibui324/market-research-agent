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
                  error: str = None) -> None:
        """Update a research job with results or status."""
        update_data = {"updated_at": datetime.utcnow()}
        if status:
            update_data["status"] = status
        if result:
            update_data["result"] = result
        if error:
            update_data["error"] = error

        self.jobs.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID."""
        job = self.jobs.find_one({"job_id": job_id})
        if job:
            return self._convert_objectid_to_str(job)
        return None

    def store_report(self, job_id: str, report_data: Dict[str, Any]) -> None:
        """Store the finalized research report with SWOT analyses."""
        self.reports.insert_one({
            "job_id": job_id,
            "report_content": report_data.get("report_content", ""),
            "swot_analyses": report_data.get("swot_analyses", {}),
            "companies_data": report_data.get("companies_data", {}),
            "main_company": report_data.get("main_company"),
            "competitors": report_data.get("competitors", []),
            "report_type": report_data.get("report_type", "competitive_analysis"),
            "created_at": datetime.utcnow()
        })

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