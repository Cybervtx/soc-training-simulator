"""
Health check and system routes for SOC Training Simulator
"""
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import text
from datetime import datetime


health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns:
        200: Application is healthy
        503: Application is unhealthy
    """
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }
    
    # Check database connection
    try:
        from backend.models import db
        db.session.execute(text('SELECT 1'))
        status['database'] = 'connected'
    except Exception as e:
        status['database'] = 'disconnected'
        status['status'] = 'unhealthy'
        status['database_error'] = str(e)
    
    # Check configuration
    try:
        config = current_app.config
        status['config'] = {
            'debug': config.get('DEBUG', False),
            'environment': config.get('FLASK_ENV', 'unknown')
        }
    except Exception:
        pass
    
    http_status = 200 if status['status'] == 'healthy' else 503
    
    return jsonify(status), http_status


@health_bp.route('/config', methods=['GET'])
def get_public_config():
    """
    Get public configuration settings
    
    Returns:
        200: Public configuration
    """
    public_config = {
        'app_name': 'SOC Training Simulator',
        'version': '1.0.0',
        'environment': current_app.config.get('FLASK_ENV', 'development'),
        'features': {
            'abuseipdb_enabled': bool(current_app.config.get('ABUSEIPDB_API_KEY')),
            'registration_enabled': True
        }
    }
    
    return jsonify(public_config), 200


@health_bp.route('/ping', methods=['GET'])
def ping():
    """
    Simple ping endpoint for load balancers
    
    Returns:
        200: Pong
    """
    return jsonify({'pong': True, 'timestamp': datetime.utcnow().isoformat()}), 200
