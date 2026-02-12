"""
AbuseIPDB routes for SOC Training Simulator
"""
from flask import Blueprint, request, jsonify, g
from backend.services.abuseipdb_service import AbuseIPDBService
from backend.services.cache_service import CacheService
from backend.services.auth_service import token_required
import ipaddress


abuseipdb_bp = Blueprint('abuseipdb', __name__, url_prefix='/api/abuseipdb')


def validate_ip_address(ip):
    """Validate that a string is a valid IP address"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


@abuseipdb_bp.route('/check', methods=['GET'])
@token_required
def check_ip():
    """
    Check an IP address for abuse reports
    
    Query parameters:
        ip: IP address to check (required)
        force_refresh: Force refresh from API (optional, default: false)
        max_age_days: Only return reports from the last N days (optional, default: 30)
        
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: IP check results
        400: Invalid input
        401: Unauthorized
        500: API error
    """
    ip = request.args.get('ip')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    max_age_days = int(request.args.get('max_age_days', 30))
    
    if not ip:
        return jsonify({'error': 'IP address is required'}), 400
    
    if not validate_ip_address(ip):
        return jsonify({'error': 'Invalid IP address format'}), 400
    
    user_id = g.current_user.id if hasattr(g, 'current_user') else None
    
    # Check if we have cached data
    if not force_refresh:
        cached = CacheService.get_cached_ip(ip)
        if cached:
            return jsonify({
                'ip': ip,
                'data': cached.to_dict(),
                'source': 'cache',
                'cached_at': cached.cached_at.isoformat() if cached.cached_at else None,
                'expires_at': cached.expires_at.isoformat() if cached.expires_at else None
            }), 200
    
    # Fetch from API
    service = AbuseIPDBService()
    data, error = service.check_ip(ip, max_age_days, user_id)
    
    if error:
        # If API fails and we have expired cache, return it anyway
        if not force_refresh:
            cached = CacheService.get_cached_ip(ip)
            if cached:
                return jsonify({
                    'ip': ip,
                    'data': cached.to_dict(),
                    'source': 'cache',
                    'cached_at': cached.cached_at.isoformat() if cached.cached_at else None,
                    'expires_at': cached.expires_at.isoformat() if cached.expires_at else None,
                    'warning': 'Returning expired cache due to API error'
                }), 200
        
        return jsonify({'error': error}), 500
    
    # Cache the response
    ttl_hours = 24
    if data and 'data' in data:
        CacheService.set_cached_ip(ip, data['data'], ttl_hours)
    
    return jsonify({
        'ip': ip,
        'data': data,
        'source': 'api'
    }), 200


@abuseipdb_bp.route('/reports', methods=['GET'])
@token_required
def get_reports():
    """
    Get detailed reports for an IP address
    
    Query parameters:
        ip: IP address to get reports for (required)
        page: Page number (optional, default: 1)
        
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Reports data
        400: Invalid input
        401: Unauthorized
        500: API error
    """
    ip = request.args.get('ip')
    page = int(request.args.get('page', 1))
    
    if not ip:
        return jsonify({'error': 'IP address is required'}), 400
    
    if not validate_ip_address(ip):
        return jsonify({'error': 'Invalid IP address format'}), 400
    
    user_id = g.current_user.id if hasattr(g, 'current_user') else None
    
    service = AbuseIPDBService()
    data, error = service.get_ip_reports(ip, page, user_id)
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'ip': ip,
        'page': page,
        'reports': data
    }), 200


@abuseipdb_bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    """
    Get general statistics from AbuseIPDB
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Statistics data
        401: Unauthorized
        500: API error
    """
    service = AbuseIPDBService()
    data, error = service.get_stats()
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({'stats': data}), 200


@abuseipdb_bp.route('/rate-limit', methods=['GET'])
@token_required
def get_rate_limit():
    """
    Get current rate limit status
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Rate limit status
        401: Unauthorized
    """
    service = AbuseIPDBService()
    status = service.get_rate_limit_status()
    
    return jsonify(status), 200


@abuseipdb_bp.route('/usage', methods=['GET'])
@token_required
def get_usage():
    """
    Get API usage statistics
    
    Query parameters:
        hours: Number of hours to look back (optional, default: 24)
        
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Usage statistics
        401: Unauthorized
    """
    hours = int(request.args.get('hours', 24))
    
    service = AbuseIPDBService()
    stats = service.get_api_usage_stats(hours)
    
    return jsonify(stats), 200


@abuseipdb_bp.route('/popular', methods=['GET'])
@token_required
def get_popular():
    """
    Get most popular cached IPs (by abuse confidence score)
    
    Query parameters:
        limit: Number of entries to return (optional, default: 10)
        
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: List of popular IPs
        401: Unauthorized
    """
    limit = int(request.args.get('limit', 10))
    
    entries = CacheService.get_popular_ips(limit)
    
    return jsonify({
        'ips': [entry.to_dict() for entry in entries],
        'count': len(entries)
    }), 200


@abuseipdb_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_ip():
    """
    Force refresh of an IP address cache
    
    Request body:
        {
            "ip": "x.x.x.x"
        }
        
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: IP refresh initiated
        400: Invalid input
        401: Unauthorized
    """
    data = request.get_json()
    
    if not data or not data.get('ip'):
        return jsonify({'error': 'IP address is required'}), 400
    
    ip = data['ip']
    
    if not validate_ip_address(ip):
        return jsonify({'error': 'Invalid IP address format'}), 400
    
    # Mark as expired so next request will refresh
    refreshed = CacheService.refresh_ip(ip)
    
    if not refreshed:
        return jsonify({'error': 'IP not found in cache'}), 404
    
    return jsonify({
        'message': 'IP marked for refresh',
        'ip': ip
    }), 200


@abuseipdb_bp.route('/cache', methods=['GET'])
@token_required
def get_cache_stats():
    """
    Get cache statistics
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Cache statistics
        401: Unauthorized
    """
    stats = CacheService.get_cache_stats()
    
    return jsonify(stats), 200


@abuseipdb_bp.route('/cache', methods=['DELETE'])
@token_required
def clear_cache():
    """
    Clear all cache entries (admin only)
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Cache cleared
        401: Unauthorized
        403: Forbidden (not admin)
    """
    # Check if user is admin
    if not hasattr(g, 'current_user') or g.current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    count = CacheService.invalidate_cache()
    
    return jsonify({
        'message': 'Cache cleared',
        'deleted_entries': count
    }), 200


@abuseipdb_bp.route('/cleanup', methods=['POST'])
@token_required
def cleanup_expired():
    """
    Clean up expired cache entries (admin only)
    
    Headers:
        Authorization: Bearer <access_token>
        
    Returns:
        200: Cleanup completed
        401: Unauthorized
        403: Forbidden (not admin)
    """
    # Check if user is admin
    if not hasattr(g, 'current_user') or g.current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    count = CacheService.cleanup_expired()
    
    return jsonify({
        'message': 'Cleanup completed',
        'deleted_entries': count
    }), 200
