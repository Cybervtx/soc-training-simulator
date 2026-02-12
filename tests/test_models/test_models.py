"""
Testes unitários para modelos de dados
"""
import pytest
from datetime import datetime, timedelta
from backend.app import create_app
from backend.models import db, User, AbuseIPDBCache, AbuseIPDBApiLog


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
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session"""
    with app.app_context():
        yield db.session


class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, app):
        """Test creating a user"""
        with app.app_context():
            user = User(
                email='test@example.com',
                nome='Test User',
                role='analyst'
            )
            user.set_password('TestPassword123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == 'test@example.com'
            assert user.nome == 'Test User'
            assert user.role == 'analyst'
            assert user.password_hash != 'TestPassword123'  # Password should be hashed
    
    def test_password_hashing(self, app):
        """Test password hashing and verification"""
        with app.app_context():
            user = User(
                email='test@example.com',
                nome='Test User',
                role='analyst'
            )
            user.set_password('TestPassword123')
            
            assert user.check_password('TestPassword123') == True
            assert user.check_password('WrongPassword') == False
    
    def test_user_to_dict(self, app):
        """Test user serialization to dictionary"""
        with app.app_context():
            user = User(
                email='test@example.com',
                nome='Test User',
                role='analyst'
            )
            user.set_password('TestPassword123')
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            
            assert 'id' in user_dict
            assert 'email' in user_dict
            assert 'nome' in user_dict
            assert 'role' in user_dict
            assert 'password_hash' not in user_dict  # Should not include password
            assert 'created_at' in user_dict
            assert 'updated_at' in user_dict
    
    def test_user_to_public_dict(self, app):
        """Test user public serialization"""
        with app.app_context():
            user = User(
                email='test@example.com',
                nome='Test User',
                role='analyst'
            )
            db.session.add(user)
            db.session.commit()
            
            public_dict = user.to_public_dict()
            
            assert 'id' in public_dict
            assert 'email' in public_dict
            assert 'nome' in public_dict
            assert 'role' in public_dict
            assert 'created_at' not in public_dict
            assert 'password_hash' not in public_dict
    
    def test_user_repr(self, app):
        """Test user string representation"""
        with app.app_context():
            user = User(email='test@example.com', nome='Test User')
            assert repr(user) == '<User test@example.com>'


class TestAbuseIPDBCacheModel:
    """Test AbuseIPDB Cache model"""
    
    def test_create_cache_entry(self, app):
        """Test creating a cache entry"""
        with app.app_context():
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=24)
            
            cache = AbuseIPDBCache(
                ip='1.2.3.4',
                reputation_score=75,
                categories=[18, 22],
                country_code='CN',
                country_name='China',
                domain='example.cn',
                last_checked=now,
                cached_at=now,
                expires_at=expires_at,
                abuse_confidence_score=75,
                total_reports=50
            )
            db.session.add(cache)
            db.session.commit()
            
            assert cache.id is not None
            assert cache.ip == '1.2.3.4'
            assert cache.reputation_score == 75
            assert cache.categories == [18, 22]
    
    def test_cache_is_expired(self, app):
        """Test cache expiration check"""
        with app.app_context():
            now = datetime.utcnow()
            
            # Not expired
            cache = AbuseIPDBCache(
                ip='1.2.3.4',
                expires_at=now + timedelta(hours=24)
            )
            assert cache.is_expired() == False
            
            # Expired
            expired_cache = AbuseIPDBCache(
                ip='5.6.7.8',
                expires_at=now - timedelta(hours=1)
            )
            assert expired_cache.is_expired() == True
    
    def test_cache_to_dict(self, app):
        """Test cache serialization"""
        with app.app_context():
            now = datetime.utcnow()
            
            cache = AbuseIPDBCache(
                ip='1.2.3.4',
                reputation_score=50,
                country_code='US',
                country_name='United States',
                expires_at=now + timedelta(hours=24),
                abuse_confidence_score=50
            )
            db.session.add(cache)
            db.session.commit()
            
            cache_dict = cache.to_dict()
            
            assert 'ip' in cache_dict
            assert 'reputation_score' in cache_dict
            assert 'country_code' in cache_dict
            assert 'is_expired' in cache_dict
    
    def test_create_from_api_response(self, app):
        """Test creating cache entry from API response"""
        with app.app_context():
            api_response = {
                'ipAddress': '1.2.3.4',
                'abuseConfidencePercentage': 85,
                'categories': [18, 22, 25],
                'countryCode': 'CN',
                'countryName': 'China',
                'domain': 'malicious.cn',
                'isWhitelisted': False,
                'usageType': 'Data Center',
                'isp': 'Example ISP',
                'numDays': 30,
                'lastReportedAt': '2024-01-15T10:00:00Z',
                'totalReports': 100,
                'numUsers': 5
            }
            
            cache = AbuseIPDBCache.create_from_api_response('1.2.3.4', api_response)
            
            assert cache.ip == '1.2.3.4'
            assert cache.abuse_confidence_score == 85
            assert cache.categories == [18, 22, 25]
            assert cache.country_code == 'CN'


class TestAbuseIPDBApiLogModel:
    """Test AbuseIPDB API Log model"""
    
    def test_create_log_entry(self, app):
        """Test creating a log entry"""
        with app.app_context():
            log = AbuseIPDBApiLog(
                endpoint='check-block',
                request_params={'ipAddress': '1.2.3.4'},
                response_status=200,
                rate_limit_remaining=950,
                rate_limit_limit=1000,
                response_time_ms=150
            )
            db.session.add(log)
            db.session.commit()
            
            assert log.id is not None
            assert log.endpoint == 'check-block'
            assert log.response_status == 200
            assert log.response_time_ms == 150
    
    def test_log_to_dict(self, app):
        """Test log serialization"""
        with app.app_context():
            log = AbuseIPDBApiLog(
                endpoint='check-block',
                response_status=200
            )
            db.session.add(log)
            db.session.commit()
            
            log_dict = log.to_dict()
            
            assert 'id' in log_dict
            assert 'endpoint' in log_dict
            assert 'response_status' in log_dict
            assert 'created_at' in log_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
