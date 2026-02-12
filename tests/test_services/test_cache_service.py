"""
Testes unitários para o serviço de cache
"""
import pytest
from datetime import datetime, timedelta
from backend.app import create_app
from backend.models import db, AbuseIPDBCache
from backend.services.cache_service import CacheService


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def cache_entry(app):
    """Create a cache entry for testing"""
    with app.app_context():
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=24)
        
        cache = AbuseIPDBCache(
            ip='192.168.1.1',
            reputation_score=50,
            categories=[18, 22],
            country_code='US',
            country_name='United States',
            domain='example.com',
            last_checked=now,
            cached_at=now,
            expires_at=expires_at,
            abuse_confidence_score=50,
            total_reports=10
        )
        db.session.add(cache)
        db.session.commit()
        
        return cache.id


class TestCacheService:
    """Test CacheService"""
    
    def test_get_cached_ip_found(self, app, cache_entry):
        """Test getting cached IP when it exists and is valid"""
        with app.app_context():
            result = CacheService.get_cached_ip('192.168.1.1')
            
            assert result is not None
            assert result.ip == '192.168.1.1'
            assert result.reputation_score == 50
    
    def test_get_cached_ip_not_found(self, app):
        """Test getting cached IP when it doesn't exist"""
        with app.app_context():
            result = CacheService.get_cached_ip('255.255.255.255')
            
            assert result is None
    
    def test_get_cached_ip_expired(self, app):
        """Test getting cached IP when it has expired"""
        with app.app_context():
            now = datetime.utcnow()
            
            expired_cache = AbuseIPDBCache(
                ip='10.0.0.1',
                expires_at=now - timedelta(hours=1)
            )
            db.session.add(expired_cache)
            db.session.commit()
            
            result = CacheService.get_cached_ip('10.0.0.1')
            
            assert result is None
    
    def test_set_cached_ip_new(self, app):
        """Test setting a new cache entry"""
        with app.app_context():
            api_data = {
                'abuseConfidencePercentage': 75,
                'categories': [18, 22, 25],
                'countryCode': 'CN',
                'countryName': 'China',
                'domain': 'test.cn',
                'isWhitelisted': False,
                'usageType': 'Data Center',
                'isp': 'Test ISP',
                'numDays': 30,
                'lastReportedAt': '2024-01-15T10:00:00Z',
                'totalReports': 100,
                'numUsers': 5
            }
            
            result = CacheService.set_cached_ip('8.8.8.8', api_data)
            
            assert result is not None
            assert result.ip == '8.8.8.8'
            assert result.abuse_confidence_score == 75
    
    def test_set_cached_ip_update(self, app, cache_entry):
        """Test updating an existing cache entry"""
        with app.app_context():
            api_data = {
                'abuseConfidencePercentage': 100,
                'categories': [18, 22, 25, 27],
                'countryCode': 'RU',
                'countryName': 'Russia',
                'domain': 'updated.ru',
                'isWhitelisted': False,
                'totalReports': 200
            }
            
            result = CacheService.set_cached_ip('192.168.1.1', api_data)
            
            assert result is not None
            assert result.ip == '192.168.1.1'
            assert result.abuse_confidence_score == 100
    
    def test_delete_cached_ip(self, app, cache_entry):
        """Test deleting a cache entry"""
        with app.app_context():
            assert CacheService.get_cached_ip('192.168.1.1') is not None
            
            deleted = CacheService.delete_cached_ip('192.168.1.1')
            
            assert deleted is True
            assert CacheService.get_cached_ip('192.168.1.1') is None
    
    def test_delete_cached_ip_not_found(self, app):
        """Test deleting a non-existent cache entry"""
        with app.app_context():
            deleted = CacheService.delete_cached_ip('255.255.255.255')
            
            assert deleted is False
    
    def test_get_cache_stats(self, app):
        """Test getting cache statistics"""
        with app.app_context():
            now = datetime.utcnow()
            
            AbuseIPDBCache(
                ip='1.1.1.1',
                expires_at=now + timedelta(hours=24)
            )
            
            AbuseIPDBCache(
                ip='2.2.2.2',
                expires_at=now - timedelta(hours=1)
            )
            
            db.session.commit()
            
            stats = CacheService.get_cache_stats()
            
            assert 'total_entries' in stats
            assert 'valid_entries' in stats
            assert 'expired_entries' in stats
            assert stats['total_entries'] == 2
    
    def test_cleanup_expired_entries(self, app):
        """Test cleaning up expired cache entries"""
        with app.app_context():
            now = datetime.utcnow()
            
            AbuseIPDBCache(
                ip='1.1.1.1',
                expires_at=now + timedelta(hours=24)
            )
            
            AbuseIPDBCache(
                ip='2.2.2.2',
                expires_at=now - timedelta(hours=1)
            )
            
            db.session.commit()
            
            deleted_count = CacheService.cleanup_expired_entries()
            
            assert deleted_count >= 1
            
            remaining = AbuseIPDBCache.query.count()
            assert remaining == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
