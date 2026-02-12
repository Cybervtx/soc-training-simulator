"""
Authentication routes for SOC Training Simulator
"""
from flask import Blueprint, request, jsonify, g
from backend.services.auth_service import AuthService, token_required
from backend.models import db


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request body:
        {
            "email": "user@example.com",
            "nome": "User Name",
            "password": "securepassword",
            "role": "analyst" (optional)
        }
        
    Returns:
        201: User created successfully
        400: Invalid input
        409: Email already registered
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    email = data.get('email')
    nome = data.get('nome')
    password = data.get('password')
    role = data.get('role', 'analyst')
    
    # Validate required fields
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not nome:
        return jsonify({'error': 'Name is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    # Register user
    user_data, error = AuthService.register_user(email, nome, password, role)
    
    if error:
        return jsonify({'error': error}), 409
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user_data
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return tokens
    
    Request body:
        {
            "email": "user@example.com",
            "password": "securepassword"
        }
        
    Returns:
        200: Login successful
        401: Invalid credentials
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    tokens, error = AuthService.login_user(email, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify({
        'message': 'Login successful',
        **tokens
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """
    Logout the current user
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Logout successful
        401: Unauthorized
    """
    user_id = g.current_user.id
    AuthService.logout_user(user_id)
    
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """
    Get the current user's profile
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: User profile
        401: Unauthorized
    """
    user = g.current_user
    
    return jsonify({
        'user': user.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token
    
    Request body:
        {
            "refresh_token": "..."
        }
        
    Returns:
        200: New access token
        401: Invalid or expired refresh token
    """
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'error': 'Refresh token is required'}), 400
    
    new_access_token, error = AuthService.refresh_access_token(data['refresh_token'])
    
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify({
        'access_token': new_access_token
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """
    Change the current user's password
    
    Headers:
        Authorization: Bearer <access_token>
        
    Request body:
        {
            "current_password": "oldpassword",
            "new_password": "newpassword"
        }
        
    Returns:
        200: Password changed successfully
        400: Invalid input
        401: Current password is incorrect
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password are required'}), 400
    
    user = g.current_user
    
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password strength
    if not AuthService.validate_password(new_password):
        return jsonify({'error': 'New password must be at least 8 characters with uppercase, lowercase, and number'}), 400
    
    # Update password
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200
