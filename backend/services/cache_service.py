"""
Cache service for SOC Training Simulator
"""
from datetime import datetime, timedelta
from backend.models.abuseipdb_cache import AbuseIPDBCache
from backend.models import db


class CacheService:
    """Cache service for managing AbuseIPDB cache"""
    
    @staticmethod
    def get_cached_ip(ip: str):
        """
        Get cached IP data if not expired
        
        Args:
            ip: IP address to look up
            
        Returns:
            AbuseIPDBCache: Cache entry if valid, None otherwise
        """
        cache_entry = AbuseIPDBCache.query.filter_by(ip=ip).first()
        
        if cache_entry and not cache_entry.is_expired():
            return cache_entry
        
        return None
    
    @staticmethod
    def set_cached_ip(ip: str, data: dict, ttl_hours: int = 24):
        """
        Set cached IP data
        
        Args:
            ip: IP address
            data: IP data from API
            ttl_hours: Time to live in hours
            
        Returns:
            AbuseIPDBCache: Created or updated cache entry
        """
        existing = AbuseIPDBCache.query.filter_by(ip=ip).first()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=ttl_hours)
        
        if existing:
            # Update existing entry
            existing.reputation_score = data.get('abuseConfidencePercentage')
            existing.categories = data.get('categories')
            existing.country_code = data.get('countryCode')
            existing.country_name = data.get('countryName')
            existing.domain = data.get('domain')
            existing.last_checked = now
            existing.cached_at = now
            existing.expires_at = expires_at
            existing.is_whitelisted = data.get('isWhitelisted', False)
            existing.usage_type = data.get('usageType')
            existing.isp = data.get('isp')
            existing.num_days = data.get('numDays')
            existing.last_report = data.get('lastReportedAt')
            existing.abuse_confidence_score = data.get('abuseConfidencePercentage')
            existing.total_reports = data.get('totalReports')
            existing.num_users = data.get('numUsers')
            
            cache_entry = existing
        else:
            # Create new entry
            cache_entry = AbuseIPDBCache(
                ip=ip,
                reputation_score=data.get('abuseConfidencePercentage'),
                categories=data.get('categories'),
                country_code=data.get('countryCode'),
                country_name=data.get('countryName'),
                domain=data.get('domain'),
                last_checked=now,
                cached_at=now,
                expires_at=expires_at,
                is_whitelisted=data.get('isWhitelisted', False),
                usage_type=data.get('usageType'),
                isp=data.get('isp'),
                num_days=data.get('numDays'),
                last_report=data.get('lastReportedAt'),
                abuse_confidence_score=data.get('abuseConfidencePercentage'),
                total_reports=data.get('totalReports'),
                num_users=data.get('numUsers')
            )
            db.session.add(cache_entry)
        
        db.session.commit()
        return cache_entry
    
    @staticmethod
    def delete_cached_ip(ip: str):
        """
        Delete cached IP entry
        
        Args:
            ip: IP address to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        cache_entry = AbuseIPDBCache.query.filter_by(ip=ip).first()
        
        if cache_entry:
            db.session.delete(cache_entry)
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def cleanup_expired():
        """
        Remove all expired cache entries
        
        Returns:
            int: Number of deleted entries
        """
        expired_count = db.session.query(AbuseIPDBCache).filter(
            AbuseIPDBCache.expires_at < datetime.utcnow()
        ).delete()
        
        db.session.commit()
        return expired_count
    
    @staticmethod
    def get_cache_stats():
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        total_entries = AbuseIPDBCache.query.count()
        expired_entries = AbuseIPDBCache.query.filter(
            AbuseIPDBCache.expires_at < datetime.utcnow()
        ).count()
        valid_entries = total_entries - expired_entries
        
        # Get statistics by country
        country_stats = db.session.query(
            AbuseIPDBCache.country_code,
            db.func.count(AbuseIPDBCache.id)
        ).group_by(AbuseIPDBCache.country_code).all()
        
        # Get high-risk IPs (score >= 50)
        high_risk_count = AbuseIPDBCache.query.filter(
            AbuseIPDBCache.abuse_confidence_score >= 50
        ).count()
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'high_risk_count': high_risk_count,
            'country_distribution': {str(k): v for k, v in country_stats}
        }
    
    @staticmethod
    def get_popular_ips(limit: int = 10):
        """
        Get most cached IPs (by abuse confidence score)
        
        Args:
            limit: Number of entries to return
            
        Returns:
            list: List of cache entries sorted by abuse confidence score
        """
        return AbuseIPDBCache.query.order_by(
            AbuseIPDBCache.abuse_confidence_score.desc()
        ).limit(limit).all()
    
    @staticmethod
    def invalidate_cache():
        """
        Clear all cache entries
        
        Returns:
            int: Number of deleted entries
        """
        count = AbuseIPDBCache.query.count()
        AbuseIPDBCache.query.delete()
        db.session.commit()
        return count
    
    @staticmethod
    def refresh_ip(ip: str):
        """
        Mark an IP cache entry as requiring refresh
        
        Args:
            ip: IP address to refresh
            
        Returns:
            bool: True if marked, False if not found
        """
        cache_entry = AbuseIPDBCache.query.filter_by(ip=ip).first()
        
        if cache_entry:
            # Set expiration to now to force refresh
            cache_entry.expires_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
