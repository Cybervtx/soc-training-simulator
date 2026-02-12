"""
AbuseIPDB API service for SOC Training Simulator
"""
import time
import requests
from flask import current_app, g
from backend.models.abuseipdb_log import AbuseIPDBApiLog
from backend.models import db


class AbuseIPDBService:
    """Service for interacting with AbuseIPDB API"""
    
    def __init__(self):
        """Initialize the service with API key from config"""
        self.api_key = current_app.config.get('ABUSEIPDB_API_KEY', '')
        self.base_url = current_app.config.get('ABUSEIPDB_BASE_URL', 'https://api.abuseipdb.com/api/v2')
        self.rate_limit_daily = current_app.config.get('ABUSEIPDB_RATE_LIMIT_DAILY', 1000)
        self.rate_limit_warning = current_app.config.get('ABUSEIPDB_RATE_LIMIT_REMAINING_WARNING', 100)
    
    def _make_request(self, endpoint: str, params: dict = None, user_id: str = None, ip_address: str = None):
        """
        Make a request to the AbuseIPDB API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            user_id: User making the request (for logging)
            ip_address: IP address of the requester (for logging)
            
        Returns:
            tuple: (response_json, error_message) or (None, error_message) on failure
        """
        if not self.api_key:
            return None, "AbuseIPDB API key not configured"
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Accept': 'application/json',
            'Key': self.api_key
        }
        
        start_time = time.time()
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the API call
            self._log_api_call(
                endpoint=endpoint,
                request_params=params,
                api_response=response,
                response_time_ms=response_time_ms,
                user_id=user_id,
                ip_address=ip_address or (g.get('ip_address') if hasattr(g, 'ip_address') else None)
            )
            
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 401:
                return None, "Invalid API key"
            elif response.status_code == 429:
                return None, "Rate limit exceeded"
            elif response.status_code == 400:
                error_msg = response.json().get('errors', [{}])[0].get('detail', 'Bad request')
                return None, error_msg
            else:
                return None, f"API error: {response.status_code}"
        
        except requests.exceptions.Timeout:
            return None, "Request timeout"
        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def _log_api_call(self, endpoint: str, request_params: dict, api_response, response_time_ms: int, user_id: str = None, ip_address: str = None):
        """
        Log an API call to the database
        
        Args:
            endpoint: API endpoint called
            request_params: Parameters sent
            api_response: Response from API
            response_time_ms: Response time in milliseconds
            user_id: User making the request
            ip_address: IP address of the requester
        """
        try:
            log_entry = AbuseIPDBApiLog(
                endpoint=endpoint,
                request_params=request_params,
                response_status=api_response.status_code if hasattr(api_response, 'status_code') else None,
                rate_limit_remaining=api_response.headers.get('X-RateLimit-Remaining') if hasattr(api_response, 'headers') else None,
                rate_limit_limit=api_response.headers.get('X-RateLimit-Limit') if hasattr(api_response, 'headers') else None,
                error_message=api_response.text if hasattr(api_response, 'status_code') and api_response.status_code >= 400 else None,
                response_time_ms=response_time_ms,
                user_id=user_id,
                ip_address=ip_address
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception:
            # Don't fail the main request if logging fails
            db.session.rollback()
    
    def check_ip(self, ip: str, max_age_days: int = 30, user_id: str = None, ip_address: str = None):
        """
        Check an IP address for abuse reports
        
        Args:
            ip: IP address to check
            max_age_days: Only return reports from the last N days
            user_id: User making the request (for logging)
            ip_address: IP address of the requester
            
        Returns:
            tuple: (ip_data_dict, error_message) or (None, error_message) on failure
        """
        params = {
            'ipAddress': ip,
            'maxDaysSinceLastInvestigation': max_age_days,
            'verbose': True
        }
        
        data, error = self._make_request('check-block', params, user_id, ip_address)
        
        if error:
            return None, error
        
        return data, None
    
    def get_ip_reports(self, ip: str, page: int = 1, user_id: str = None, ip_address: str = None):
        """
        Get detailed reports for an IP address
        
        Args:
            ip: IP address to get reports for
            page: Page number for pagination
            user_id: User making the request (for logging)
            ip_address: IP address of the requester
            
        Returns:
            tuple: (reports_dict, error_message) or (None, error_message) on failure
        """
        params = {
            'ipAddress': ip,
            'page': page
        }
        
        data, error = self._make_request('reports', params, user_id, ip_address)
        
        if error:
            return None, error
        
        return data, None
    
    def get_stats(self, user_id: str = None, ip_address: str = None):
        """
        Get general statistics from AbuseIPDB
        
        Args:
            user_id: User making the request (for logging)
            ip_address: IP address of the requester
            
        Returns:
            tuple: (stats_dict, error_message) or (None, error_message) on failure
        """
        data, error = self._make_request('stats', {}, user_id, ip_address)
        
        if error:
            return None, error
        
        return data, None
    
    def get_rate_limit_status(self):
        """
        Get current rate limit status
        
        Returns:
            dict: Rate limit status information
        """
        # Get the most recent log entry to check rate limit
        latest_log = AbuseIPDBApiLog.query.order_by(
            AbuseIPDBApiLog.created_at.desc()
        ).first()
        
        if latest_log and latest_log.rate_limit_remaining is not None:
            remaining = int(latest_log.rate_limit_remaining)
            limit = int(latest_log.rate_limit_limit) if latest_log.rate_limit_limit else self.rate_limit_daily
            
            return {
                'remaining': remaining,
                'limit': limit,
                'usage_percentage': ((limit - remaining) / limit * 100) if limit > 0 else 0,
                'is_critical': remaining <= self.rate_limit_warning
            }
        
        # If no log entries, assume full quota
        return {
            'remaining': self.rate_limit_daily,
            'limit': self.rate_limit_daily,
            'usage_percentage': 0,
            'is_critical': False
        }
    
    def get_api_usage_stats(self, hours: int = 24):
        """
        Get API usage statistics for the last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            dict: API usage statistics
        """
        from datetime import datetime, timedelta
        from backend.models import db
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Total requests
        total_requests = AbuseIPDBApiLog.query.filter(
            AbuseIPDBApiLog.created_at > cutoff
        ).count()
        
        # Failed requests
        failed_requests = AbuseIPDBApiLog.query.filter(
            AbuseIPDBApiLog.created_at > cutoff,
            AbuseIPDBApiLog.response_status >= 400
        ).count()
        
        # Average response time
        avg_response_time = db.session.query(
            db.func.avg(AbuseIPDBApiLog.response_time_ms)
        ).filter(
            AbuseIPDBApiLog.created_at > cutoff
        ).scalar()
        
        # Requests by endpoint
        by_endpoint = db.session.query(
            AbuseIPDBApiLog.endpoint,
            db.func.count(AbuseIPDBApiLog.id)
        ).filter(
            AbuseIPDBApiLog.created_at > cutoff
        ).group_by(AbuseIPDBApiLog.endpoint).all()
        
        # Requests by hour
        by_hour = db.session.query(
            db.func.date_trunc('hour', AbuseIPDBApiLog.created_at),
            db.func.count(AbuseIPDBApiLog.id)
        ).filter(
            AbuseIPDBApiLog.created_at > cutoff
        ).group_by(db.func.date_trunc('hour', AbuseIPDBApiLog.created_at)).all()
        
        return {
            'period_hours': hours,
            'total_requests': total_requests,
            'failed_requests': failed_requests,
            'success_rate': ((total_requests - failed_requests) / total_requests * 100) if total_requests > 0 else 100,
            'avg_response_time_ms': round(avg_response_time, 2) if avg_response_time else 0,
            'by_endpoint': {str(k): v for k, v in by_endpoint},
            'by_hour': {str(k): v for k, v in by_hour}
        }
