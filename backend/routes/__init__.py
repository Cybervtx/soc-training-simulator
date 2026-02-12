# Routes initialization
from backend.routes.auth import auth_bp
from backend.routes.abuseipdb import abuseipdb_bp
from backend.routes.health import health_bp
from backend.routes.scenarios import scenarios_bp
from backend.routes.investigation import investigation_bp

__all__ = ['auth_bp', 'abuseipdb_bp', 'health_bp', 'scenarios_bp', 'investigation_bp']
