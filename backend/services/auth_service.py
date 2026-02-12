"""
Authentication service for SOC Training Simulator
"""
from datetime import datetime, timedelta
from functools import wraps
import jwt
from flask import current_app, g, request, jsonify
from backend.models.user import User
from backend.models import db
import re


class AuthService:
    """Authentication service for handling user authentication and authorization"""
    
    @staticmethod
    def register_user(email: str, nome: str, password: str, role: str = 'analyst'):
        """
        Register a new user
        
        Args:
            email: User's email address
            nome: User's name
            password: User's password
            role: User's role (analyst, instructor, admin)
            
        Returns:
            tuple: (user_dict, error_message) or (None, error_message) on failure
        """
        # Validate email format
        if not AuthService.validate_email(email):
            return None, "Invalid email format"
        
        # Validate password strength
        if not AuthService.validate_password(password):
            return None, "Password must be at least 8 characters with uppercase, lowercase, and number"
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return None, "Email already registered"
        
        # Validate role
        valid_roles = ['analyst', 'instructor', 'admin']
        if role not in valid_roles:
            role = 'analyst'
        
        # Create new user
        user = User(
            email=email,
            nome=nome,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return user.to_dict(), None
    
    @staticmethod
    def login_user(email: str, password: str):
        """
        Authenticate a user and return tokens
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            tuple: (tokens_dict, error_message) or (None, error_message) on failure
        """
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return None, "Invalid email or password"
        
        if not user.check_password(password):
            return None, "Invalid email or password"
        
        # Generate tokens
        access_token = AuthService.generate_access_token(user)
        refresh_token = AuthService.generate_refresh_token(user)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }, None
    
    @staticmethod
    def logout_user(user_id: str):
        """
        Logout user (invalidate tokens - would need token blacklist in production)
        
        Args:
            user_id: User's ID
            
        Returns:
            bool: True on success
        """
        # In production, you would add the token to a blacklist
        # For now, we just return success as JWT tokens are stateless
        return True
    
    @staticmethod
    def refresh_access_token(refresh_token: str):
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            tuple: (new_access_token, error_message) or (None, error_message) on failure
        """
        try:
            payload = jwt.decode(
                refresh_token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256'],
                options={'verify_exp': False}  # We'll check exp manually
            )
            
            user_id = payload.get('sub')
            if not user_id:
                return None, "Invalid token"
            
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            # Generate new access token
            new_access_token = AuthService.generate_access_token(user)
            
            return new_access_token, None
        
        except jwt.ExpiredSignatureError:
            return None, "Refresh token expired"
        except jwt.InvalidTokenError:
            return None, "Invalid token"
    
    @staticmethod
    def get_user_by_id(user_id: str):
        """
        Get user by ID
        
        Args:
            user_id: User's ID
            
        Returns:
            User: User object or None
        """
        return User.query.get(user_id)
    
    @staticmethod
    def generate_access_token(user: User) -> str:
        """
        Generate JWT access token
        
        Args:
            user: User object
            
        Returns:
            str: JWT access token
        """
        expires_hours = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24)
        expires_delta = timedelta(hours=expires_hours)
        
        payload = {
            'sub': user.id,
            'email': user.email,
            'role': user.role,
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + expires_delta
        }
        
        token = jwt.encode(
            payload, 
            current_app.config['JWT_SECRET_KEY'], 
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def generate_refresh_token(user: User) -> str:
        """
        Generate JWT refresh token
        
        Args:
            user: User object
            
        Returns:
            str: JWT refresh token
        """
        expires_days = current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 7)
        expires_delta = timedelta(days=expires_days)
        
        payload = {
            'sub': user.id,
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + expires_delta
        }
        
        token = jwt.encode(
            payload, 
            current_app.config['JWT_SECRET_KEY'], 
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode JWT token
        
        Args:
            token: JWT token
            
        Returns:
            dict: Token payload or empty dict on failure
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address
            
        Returns:
            bool: True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """
        Validate password strength
        
        Args:
            password: Password
            
        Returns:
            bool: True if valid, False otherwise
        """
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True


def token_required(f):
    """
    Decorator to require authentication for a route
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            payload = AuthService.decode_token(token)
            
            if 'error' in payload:
                return jsonify({'error': payload['error']}), 401
            
            user_id = payload.get('sub')
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            g.current_user = user
            g.token_payload = payload
        
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


def role_required(*allowed_roles):
    """
    Decorator to require specific roles for a route
    
    Args:
        allowed_roles: List of allowed roles
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user = g.current_user
            
            if user.role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


def admin_required(f):
    """
    Decorator to require admin role for a route
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        
        user = g.current_user
        
        if user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated
