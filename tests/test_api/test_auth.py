"""
Testes unitários para autenticação
"""
import pytest
import json
from backend.app import create_app
from backend.models import db, User


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
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            nome='Test User',
            role='analyst'
        )
        user.set_password('TestPassword123')
        db.session.add(user)
        db.session.commit()
        
        return user.id


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_ping(self, client):
        """Test ping endpoint"""
        response = client.get('/api/ping')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'pong' in data
        assert data['pong'] == True
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
    
    def test_public_config(self, client):
        """Test public config endpoint"""
        response = client.get('/api/config')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'app_name' in data
        assert data['app_name'] == 'SOC Training Simulator'


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/api/auth/register',
            data=json.dumps({
                'email': 'newuser@example.com',
                'nome': 'New User',
                'password': 'NewPassword123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['email'] == 'newuser@example.com'
        assert data['user']['role'] == 'analyst'
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post('/api/auth/register',
            data=json.dumps({
                'email': 'test@example.com',
                'nome': 'Duplicate User',
                'password': 'Password123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post('/api/auth/register',
            data=json.dumps({
                'email': 'invalid-email',
                'nome': 'Test User',
                'password': 'Password123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 409
    
    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post('/api/auth/register',
            data=json.dumps({
                'email': 'test@example.com',
                'nome': 'Test User',
                'password': 'weak'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 409
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'WrongPassword'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'nonexistent@example.com',
                'password': 'Password123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_get_profile_without_token(self, client):
        """Test getting profile without token"""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
    
    def test_get_profile_with_token(self, client, test_user):
        """Test getting profile with valid token"""
        # First login to get token
        login_response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }),
            content_type='application/json'
        )
        
        tokens = json.loads(login_response.data)
        
        # Then access profile
        response = client.get('/api/auth/me',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['email'] == 'test@example.com'
    
    def test_refresh_token(self, client, test_user):
        """Test refreshing access token"""
        # First login to get refresh token
        login_response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }),
            content_type='application/json'
        )
        
        tokens = json.loads(login_response.data)
        
        # Refresh token
        response = client.post('/api/auth/refresh',
            data=json.dumps({
                'refresh_token': tokens['refresh_token']
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'access_token' in data
    
    def test_change_password(self, client, test_user):
        """Test changing password"""
        # First login to get token
        login_response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }),
            content_type='application/json'
        )
        
        tokens = json.loads(login_response.data)
        
        # Change password
        response = client.post('/api/auth/change-password',
            data=json.dumps({
                'current_password': 'TestPassword123',
                'new_password': 'NewPassword456'
            }),
            headers={'Authorization': f"Bearer {tokens['access_token']}"},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Login with new password
        login_response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'NewPassword456'
            }),
            content_type='application/json'
        )
        
        assert login_response.status_code == 200


class TestAbuseIPDBEndpoints:
    """Test AbuseIPDB endpoints"""
    
    def test_check_ip_without_auth(self, client):
        """Test checking IP without authentication"""
        response = client.get('/api/abuseipdb/check?ip=1.2.3.4')
        assert response.status_code == 401
    
    def test_get_stats_without_auth(self, client):
        """Test getting stats without authentication"""
        response = client.get('/api/abuseipdb/stats')
        assert response.status_code == 401
    
    def test_get_cache_stats_without_auth(self, client):
        """Test getting cache stats without authentication"""
        response = client.get('/api/abuseipdb/cache')
        assert response.status_code == 401
    
    def test_check_ip_with_invalid_ip(self, client, test_user):
        """Test checking IP with invalid IP format"""
        # First login to get token
        login_response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }),
            content_type='application/json'
        )
        
        tokens = json.loads(login_response.data)
        
        # Check invalid IP
        response = client.get('/api/abuseipdb/check?ip=invalid-ip',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_check_ip_missing_param(self, client, test_user):
        """Test checking IP without IP parameter"""
        # First login to get token
        login_response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'TestPassword123'
            }),
            content_type='application/json'
        )
        
        tokens = json.loads(login_response.data)
        
        # Check without IP
        response = client.get('/api/abuseipdb/check',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        
        assert response.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
