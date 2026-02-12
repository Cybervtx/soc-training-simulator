"""
AbuseIPDB Cache model for storing IP reputation data
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AbuseIPDBCache(db.Model):
    """Cache model for storing AbuseIPDB lookup results"""
    
    __tablename__ = 'abuseipdb_cache'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip = db.Column(db.String(45), unique=True, nullable=False, index=True)
    reputation_score = db.Column(db.Integer, nullable=True)
    categories = db.Column(db.ARRAY(db.Integer), nullable=True)
    country_code = db.Column(db.String(2), nullable=True)
    country_name = db.Column(db.String(100), nullable=True)
    domain = db.Column(db.String(255), nullable=True)
    last_checked = db.Column(db.DateTime, nullable=False)
    cached_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    is_whitelisted = db.Column(db.Boolean, default=False)
    usage_type = db.Column(db.String(50), nullable=True)
    isp = db.Column(db.String(255), nullable=True)
    num_days = db.Column(db.Integer, nullable=True)
    last_report = db.Column(db.DateTime, nullable=True)
    
    # Additional fields from API response
    abuse_confidence_score = db.Column(db.Integer, nullable=True)
    total_reports = db.Column(db.Integer, nullable=True)
    num_users = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<AbuseIPDBCache {self.ip}>'
    
    def is_expired(self):
        """Check if the cache entry is expired"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        """Convert cache entry to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ip': self.ip,
            'reputation_score': self.reputation_score,
            'categories': self.categories,
            'country_code': self.country_code,
            'country_name': self.country_name,
            'domain': self.domain,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_whitelisted': self.is_whitelisted,
            'usage_type': self.usage_type,
            'isp': self.isp,
            'num_days': self.num_days,
            'last_report': self.last_report.isoformat() if self.last_report else None,
            'abuse_confidence_score': self.abuse_confidence_score,
            'total_reports': self.total_reports,
            'num_users': self.num_users,
            'is_expired': self.is_expired()
        }
    
    @classmethod
    def create_from_api_response(cls, ip: str, api_response: dict, ttl_hours: int = 24):
        """Create a new cache entry from API response"""
        now = datetime.utcnow()
        expires_at = now.replace(hour=ttl_hours)
        
        return cls(
            ip=ip,
            reputation_score=api_response.get('abuseConfidencePercentage', 0),
            categories=api_response.get('categories', []),
            country_code=api_response.get('countryCode'),
            country_name=api_response.get('countryName'),
            domain=api_response.get('domain'),
            last_checked=now,
            cached_at=now,
            expires_at=expires_at,
            is_whitelisted=api_response.get('isWhitelisted', False),
            usage_type=api_response.get('usageType'),
            isp=api_response.get('isp'),
            num_days=api_response.get('numDays'),
            last_report=api_response.get('lastReportedAt'),
            abuse_confidence_score=api_response.get('abuseConfidencePercentage'),
            total_reports=api_response.get('totalReports'),
            num_users=api_response.get('numUsers')
        )
