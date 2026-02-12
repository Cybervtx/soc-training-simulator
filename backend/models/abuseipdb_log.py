"""
AbuseIPDB API Log model for tracking API usage
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class AbuseIPDBApiLog(db.Model):
    """Log model for tracking AbuseIPDB API usage"""
    
    __tablename__ = 'abuseipdb_api_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    endpoint = db.Column(db.String(100), nullable=False)
    request_params = db.Column(db.JSON, nullable=True)
    response_status = db.Column(db.Integer, nullable=True)
    rate_limit_remaining = db.Column(db.Integer, nullable=True)
    rate_limit_limit = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    response_time_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_id = db.Column(db.String(36), nullable=True)
    
    def __repr__(self):
        return f'<AbuseIPDBApiLog {self.endpoint} {self.created_at}>'
    
    def to_dict(self):
        """Convert log entry to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'request_params': self.request_params,
            'response_status': self.response_status,
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_limit': self.rate_limit_limit,
            'error_message': self.error_message,
            'response_time_ms': self.response_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ip_address': self.ip_address,
            'user_id': self.user_id
        }
    
    @classmethod
    def create_from_api_response(cls, endpoint: str, request_params: dict, api_response, response_time_ms: int, user_id: str = None, ip_address: str = None):
        """Create a new log entry from API response"""
        return cls(
            endpoint=endpoint,
            request_params=request_params,
            response_status=api_response.status_code if hasattr(api_response, 'status_code') else None,
            rate_limit_remaining=api_response.headers.get('X-RateLimit-Remaining') if hasattr(api_response, 'headers') else None,
            rate_limit_limit=api_response.headers.get('X-RateLimit-Limit') if hasattr(api_response, 'headers') else None,
            error_message=api_response.text if hasattr(api_response, 'status_code') and api_response.status_code >= 400 else None,
            response_time_ms=response_time_ms,
            user_id=user_id,
            ip_address=ip_address
        )
