"""
Investigation Tools Routes - SOC Training Simulator (Parte 2)
API endpoints for enrichment tools: WHOIS, Geolocation, pDNS, etc.
"""

import uuid
from flask import Blueprint, request, jsonify
import sys
sys.path.insert(0, '/workspaces/soc-training-simulator')

from backend.services.investigation_tools_service import InvestigationToolsService


# Create blueprint
investigation_bp = Blueprint('investigation', __name__, url_prefix='/api/tools')

# Service instance
investigation_service = InvestigationToolsService()


@investigation_bp.route('/geoip', methods=['GET'])
def geoip_lookup():
    """
    Get geolocation data for an IP address
    
    Query params:
    - ip: IP address to look up
    """
    ip = request.args.get('ip') or request.args.get('query')
    
    if not ip:
        return jsonify({
            'success': False,
            'error': 'IP address is required (query param: ip or query)'
        }), 400
    
    try:
        data = investigation_service.geolocation_lookup(ip)
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@investigation_bp.route('/whois', methods=['GET'])
def whois_lookup():
    """
    Get WHOIS data for a domain
    
    Query params:
    - domain: Domain name to look up
    """
    domain = request.args.get('domain') or request.args.get('query')
    
    if not domain:
        return jsonify({
            'success': False,
            'error': 'Domain is required (query param: domain or query)'
        }), 400
    
    try:
        data = investigation_service.whois_lookup(domain)
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@investigation_bp.route('/pdns', methods=['GET'])
def pdns_lookup():
    """
    Get passive DNS records for a domain
    
    Query params:
    - domain: Domain name to look up
    """
    domain = request.args.get('domain') or request.args.get('query')
    
    if not domain:
        return jsonify({
            'success': False,
            'error': 'Domain is required (query param: domain or query)'
        }), 400
    
    try:
        data = investigation_service.pdns_lookup(domain)
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@investigation_bp.route('/reverse-dns', methods=['GET'])
def reverse_dns():
    """
    Get reverse DNS (hostname) for an IP address
    
    Query params:
    - ip: IP address to look up
    """
    ip = request.args.get('ip') or request.args.get('query')
    
    if not ip:
        return jsonify({
            'success': False,
            'error': 'IP address is required (query param: ip or query)'
        }), 400
    
    try:
        hostname = investigation_service.reverse_dns_lookup(ip)
        
        return jsonify({
            'success': True,
            'data': {
                'ip': ip,
                'hostname': hostname
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@investigation_bp.route('/shodan', methods=['GET'])
def shodan_lookup():
    """
    Get simulated Shodan data for an IP address
    
    Query params:
    - ip: IP address to look up
    """
    ip = request.args.get('ip') or request.args.get('query')
    
    if not ip:
        return jsonify({
            'success': False,
            'error': 'IP address is required (query param: ip or query)'
        }), 400
    
    try:
        data = investigation_service.shodan_lookup(ip)
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@investigation_bp.route('/enrich', methods=['GET'])
def enrich_artifact():
    """
    Enrich an artifact with all available data
    
    Query params:
    - type: Artifact type (ip, domain, url)
    - value: Artifact value
    """
    artifact_type = request.args.get('type')
    value = request.args.get('value') or request.args.get('query')
    
    if not artifact_type or not value:
        return jsonify({
            'success': False,
            'error': 'Both type and value are required (query params: type, value)'
        }), 400
    
    try:
        data = investigation_service.enrich_artifact(artifact_type, value)
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@investigation_bp.route('/batch', methods=['POST'])
def batch_enrich():
    """
    Enrich multiple artifacts in a single request
    
    Body:
    {
        "artifacts": [
            {"type": "ip", "value": "185.220.101.42"},
            {"type": "domain", "value": "malware-c2.badssl.com"}
        ]
    }
    """
    try:
        data = request.get_json() or {}
        artifacts = data.get('artifacts', [])
        
        if not artifacts:
            return jsonify({
                'success': False,
                'error': 'No artifacts provided'
            }), 400
        
        results = []
        for artifact in artifacts:
            artifact_type = artifact.get('type')
            value = artifact.get('value')
            
            if artifact_type and value:
                enrichment = investigation_service.enrich_artifact(artifact_type, value)
                results.append(enrichment)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
