"""
SOC Training Simulator - Flask Application

A training simulator for Security Operations Center (SOC) analysts.
This is Part 1: Foundation (MVP Core)

Author: SOC Training Team
Version: 1.0.0
"""

import os
import logging
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend.config import get_config
from backend.models import db
from backend.routes import auth_bp, abuseipdb_bp, health_bp, scenarios_bp, investigation_bp


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """
    Application factory for creating Flask app instances
    
    Args:
        config: Configuration class to use (optional)
        
    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = get_config()
    
    app.config.from_object(config)
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(abuseipdb_bp)
    app.register_blueprint(scenarios_bp)
    app.register_blueprint(investigation_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'Server error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
    
    # Serve frontend files
    @app.route('/')
    def index():
        """Serve the main index.html"""
        return send_from_directory('../frontend', 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        """Serve static files from frontend directory"""
        # Check if it's an API route
        if path.startswith('api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        
        # Serve frontend files
        return send_from_directory('../frontend', path)
    
    # Add CORS headers to all responses
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    logger.info('SOC Training Simulator initialized successfully')
    
    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
