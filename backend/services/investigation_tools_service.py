"""
Investigation Tools Service - SOC Training Simulator (Parte 2)
Service for simulated enrichment tools: WHOIS, Geolocation, pDNS, etc.
"""

import uuid
import random
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from ipaddress import ip_address, IPv4Address
import sys
sys.path.insert(0, '/workspaces/soc-training-simulator')

from backend.config import get_config
from backend.models.scenario import EnrichedDataCache


class InvestigationToolsService:
    """Service for simulated investigation tools"""
    
    # Realistic data for simulation
    COUNTRIES = {
        'DE': {'name': 'Germany', 'code': 'DE', 'latitude': 51.1657, 'longitude': 10.4515},
        'US': {'name': 'United States', 'code': 'US', 'latitude': 37.0902, 'longitude': -95.7129},
        'RU': {'name': 'Russia', 'code': 'RU', 'latitude': 61.5240, 'longitude': 105.3188},
        'CN': {'name': 'China', 'code': 'CN', 'latitude': 35.8617, 'longitude': 104.1954},
        'BR': {'name': 'Brazil', 'code': 'BR', 'latitude': -14.2350, 'longitude': -51.9253},
        'NL': {'name': 'Netherlands', 'code': 'NL', 'latitude': 52.1326, 'longitude': 5.2913},
        'FR': {'name': 'France', 'code': 'FR', 'latitude': 46.2276, 'longitude': 2.2137},
        'UA': {'name': 'Ukraine', 'code': 'UA', 'latitude': 48.3794, 'longitude': 31.1656},
        'KR': {'name': 'South Korea', 'code': 'KR', 'latitude': 35.9078, 'longitude': 127.7669},
        'JP': {'name': 'Japan', 'code': 'JP', 'latitude': 36.2048, 'longitude': 138.2529},
    }
    
    ISP_DATA = {
        '185.220.101.42': {'isp': 'Tor Exit Node', 'asn': 'AS60068', 'org': 'DataWire Inc'},
        '91.219.236.166': {'isp': 'Global Layer', 'asn': 'AS49453', 'org': 'Global Layer LLC'},
        '45.227.254.12': {'isp': '.host', 'asn': 'AS202425', 'org': 'IP Volume inc'},
        '8.8.8.8': {'isp': 'Google LLC', 'asn': 'AS15169', 'org': 'Google LLC'},
        '1.1.1.1': {'isp': 'Cloudflare, Inc.', 'asn': 'AS13335', 'org': 'Cloudflare, Inc.'},
    }
    
    # Realistic WHOIS data
    WHOIS_DATA = {
        'malware-c2.badssl.com': {
            'domain': 'malware-c2.badssl.com',
            'registrar': 'NameCheap, Inc.',
            'created_date': '2024-01-15',
            'expires_date': '2025-01-15',
            'nameservers': [
                'ns1.cloudprovider.com',
                'ns2.cloudprovider.com',
                'ns3.cloudprovider.com'
            ],
            'whois_server': 'whois.namecheap.com',
            'status': 'clientTransferProhibited',
            ' registrant_country': 'RU',
            'admin_country': 'RU',
            'tech_country': 'RU',
        },
        'phishing-test.example.com': {
            'domain': 'phishing-test.example.com',
            'registrar': 'GoDaddy.com, LLC',
            'created_date': '2023-06-20',
            'expires_date': '2025-06-20',
            'nameservers': [
                'ns1.example-dns.com',
                'ns2.example-dns.com'
            ],
            'whois_server': 'whois.godaddy.com',
            'status': 'ok',
            'registrant_country': 'CN',
            'admin_country': 'CN',
            'tech_country': 'CN',
        },
    }
    
    # Malicious IPs patterns
    MALICIOUS_IP_RANGES = [
        ('185.220.0.0', '185.220.255.255'),  # Tor exit nodes
        ('91.219.0.0', '91.219.255.255'),    # Known malicious
        ('45.227.0.0', '45.227.255.255'),    # Known malicious
    ]
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.config = get_config()
        self.cache_duration = timedelta(hours=24)
    
    def geolocation_lookup(self, ip: str) -> Dict[str, Any]:
        """
        Simulate geolocation lookup for an IP address
        
        Returns realistic geolocation data for training purposes
        """
        # Check cache first
        cached = self._get_cached_data('geolocation', ip)
        if cached:
            return cached
        
        # Generate geolocation data
        data = self._generate_geolocation(ip)
        
        # Cache the result
        self._cache_data('geolocation', ip, data)
        
        return data
    
    def _generate_geolocation(self, ip: str) -> Dict[str, Any]:
        """Generate realistic geolocation data"""
        # Validate IP
        try:
            ip_obj = ip_address(ip)
            is_private = ip_obj.is_private
        except ValueError:
            is_private = False
        
        if is_private:
            return {
                'ip': ip,
                'country_code': 'XX',
                'country_name': 'Private Network',
                'city': 'Internal Network',
                'latitude': 0.0,
                'longitude': 0.0,
                'isp': 'Internal',
                'as_number': 'Private',
                'as_name': 'Private Network',
                'is_private': True,
                'is_malicious': False,
                'usage_type': 'Internal',
                'threat_level': 'none'
            }
        
        # Check if IP is in known malicious ranges
        is_malicious = self._is_known_malicious_ip(ip)
        
        # Get country from IP hash for consistency
        ip_hash = hash(ip)
        country_codes = list(self.COUNTRIES.keys())
        country = self.COUNTRIES[country_codes[ip_hash % len(country_codes)]]
        
        # Generate city based on country
        cities = {
            'DE': 'Frankfurt',
            'US': 'New York',
            'RU': 'Moscow',
            'CN': 'Beijing',
            'BR': 'São Paulo',
            'NL': 'Amsterdam',
            'FR': 'Paris',
            'UA': 'Kyiv',
            'KR': 'Seoul',
            'JP': 'Tokyo',
        }
        
        city = cities.get(country['code'], 'Unknown City')
        
        # Get ISP data
        isp_info = self.ISP_DATA.get(ip, {
            'isp': f'ISP {ip_hash % 1000}',
            'asn': f'AS{abs(ip_hash) % 100000}',
            'org': f'Organization {abs(ip_hash) % 100}'
        })
        
        return {
            'ip': ip,
            'country_code': country['code'],
            'country_name': country['name'],
            'city': city,
            'latitude': country['latitude'] + random.uniform(-2, 2),
            'longitude': country['longitude'] + random.uniform(-2, 2),
            'isp': isp_info['isp'],
            'as_number': isp_info['asn'],
            'as_name': isp_info.get('org', ''),
            'is_private': False,
            'is_malicious': is_malicious,
            'usage_type': self._get_usage_type(is_malicious),
            'threat_level': 'high' if is_malicious else 'low',
            'abuse_confidence_score': random.randint(50, 100) if is_malicious else random.randint(0, 30),
            'total_reports': random.randint(10, 500) if is_malicious else random.randint(0, 10),
            'last_reported': (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat(),
        }
    
    def _is_known_malicious_ip(self, ip: str) -> bool:
        """Check if IP is in known malicious ranges"""
        try:
            ip_obj = ip_address(ip)
            for start, end in self.MALICIOUS_IP_RANGES:
                start_ip = ip_address(start)
                end_ip = ip_address(end)
                if start_ip <= ip_obj <= end_ip:
                    return True
        except ValueError:
            pass
        return False
    
    def _get_usage_type(self, is_malicious: bool) -> str:
        """Get typical usage type based on malicious status"""
        if is_malicious:
            return random.choice(['VPN/Tor', 'Hosting', 'ISP', 'Data Center'])
        return random.choice(['Commercial', 'Residential', 'Educational', 'Government'])
    
    def whois_lookup(self, domain: str) -> Dict[str, Any]:
        """
        Simulate WHOIS lookup for a domain
        
        Returns realistic WHOIS data for training purposes
        """
        # Check cache first
        cached = self._get_cached_data('whois', domain)
        if cached:
            return cached
        
        # Generate WHOIS data
        data = self._generate_whois(domain)
        
        # Cache the result
        self._cache_data('whois', domain, data)
        
        return data
    
    def _generate_whois(self, domain: str) -> Dict[str, Any]:
        """Generate realistic WHOIS data"""
        # Check for known domains
        if domain in self.WHOIS_DATA:
            return self.WHOIS_DATA[domain]
        
        # Generate based on domain pattern
        is_suspicious = any(word in domain.lower() for word in [
            'malware', 'c2', 'phishing', 'evil', 'bad', 'test', 'secure'
        ])
        
        registrars = [
            'NameCheap, Inc.',
            'GoDaddy.com, LLC',
            'Tucows Domains Inc.',
            'Domain.com, LLC',
            'Name.com, Inc.',
        ]
        
        countries = ['US', 'CN', 'RU', 'BR', 'NL', 'DE', 'UA']
        
        # Generate creation date
        created_days_ago = random.randint(30, 730)
        created_date = (datetime.utcnow() - timedelta(days=created_days_ago)).strftime('%Y-%m-%d')
        expires_days = random.randint(365, 730)
        expires_date = (datetime.utcnow() + timedelta(days=expires_days)).strftime('%Y-%m-%d')
        
        return {
            'domain': domain,
            'registrar': random.choice(registrars),
            'created_date': created_date,
            'expires_date': expires_date,
            'nameservers': [
                f'ns1.{random.choice(["cloud", "dns", "net", "host"])}provider.com',
                f'ns2.{random.choice(["cloud", "dns", "net", "host"])}provider.com',
            ],
            'whois_server': 'whois.registrar.com',
            'status': 'clientTransferProhibited' if is_suspicious else 'ok',
            'registrant_country': random.choice(countries),
            'admin_country': random.choice(countries),
            'tech_country': random.choice(countries),
            'is_suspicious': is_suspicious,
            'threat_indicators': self._get_threat_indicators(domain) if is_suspicious else [],
        }
    
    def _get_threat_indicators(self, domain: str) -> List[str]:
        """Generate threat indicators for suspicious domains"""
        indicators = []
        if 'c2' in domain.lower():
            indicators.append('Domain associated with C2 infrastructure')
        if 'phish' in domain.lower():
            indicators.append('Domain associated with phishing campaigns')
        if 'malware' in domain.lower():
            indicators.append('Domain associated with malware distribution')
        if 'test' in domain.lower():
            indicators.append('Test domain - potentially used for malicious testing')
        if not indicators:
            indicators.append('Domain pattern matches known malicious domains')
        return indicators
    
    def pdns_lookup(self, domain: str) -> Dict[str, Any]:
        """
        Simulate passive DNS lookup for a domain
        
        Returns realistic DNS records for training purposes
        """
        # Check cache first
        cached = self._get_cached_data('pdns', domain)
        if cached:
            return cached
        
        # Generate DNS data
        data = self._generate_pdns(domain)
        
        # Cache the result
        self._cache_data('pdns', domain, data)
        
        return data
    
    def _generate_pdns(self, domain: str) -> Dict[str, Any]:
        """Generate realistic passive DNS data"""
        # Determine if domain is suspicious
        is_suspicious = any(word in domain.lower() for word in [
            'malware', 'c2', 'phishing', 'evil', 'bad', 'test'
        ])
        
        records = []
        
        # A records
        if is_suspicious:
            a_ips = ['185.220.101.42', '91.219.236.166', '45.227.254.12']
        else:
            a_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for ip in a_ips[:random.randint(1, 3)]:
            first_seen = (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat()
            last_seen = (datetime.utcnow() - timedelta(days=random.randint(0, 7))).isoformat()
            records.append({
                'type': 'A',
                'value': ip,
                'first_seen': first_seen,
                'last_seen': last_seen,
            })
        
        # AAAA records (if not suspicious)
        if not is_suspicious:
            aaaa_ips = ['2001:db8::1', '2001:db8::2']
            for ip in aaaa_ips[:1]:
                first_seen = (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat()
                last_seen = (datetime.utcnow() - timedelta(days=random.randint(0, 7))).isoformat()
                records.append({
                    'type': 'AAAA',
                    'value': ip,
                    'first_seen': first_seen,
                    'last_seen': last_seen,
                })
        
        # MX records
        mx_hosts = [f'mail.{domain}', f'smtp.{domain}', 'mail.google.com']
        for host in mx_hosts[:random.randint(1, 2)]:
            first_seen = (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat()
            records.append({
                'type': 'MX',
                'value': host,
                'priority': random.randint(10, 50),
                'first_seen': first_seen,
            })
        
        # NS records
        ns_hosts = [f'ns1.{domain}', f'ns2.{domain}']
        for host in ns_hosts:
            first_seen = (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat()
            records.append({
                'type': 'NS',
                'value': host,
                'first_seen': first_seen,
            })
        
        # TXT records
        txt_records = ['v=spf1 include:_spf.google.com ~all']
        if is_suspicious:
            txt_records.append('v=spf1 -all')
        
        for txt in txt_records:
            first_seen = (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat()
            records.append({
                'type': 'TXT',
                'value': txt,
                'first_seen': first_seen,
            })
        
        return {
            'domain': domain,
            'records': records,
            'total_records': len(records),
            'is_suspicious': is_suspicious,
            'threat_indicators': self._get_pdns_threat_indicators(records) if is_suspicious else [],
        }
    
    def _get_pdns_threat_indicators(self, records: List[Dict]) -> List[str]:
        """Generate threat indicators for DNS records"""
        indicators = []
        for record in records:
            if record['type'] == 'A':
                ip = record.get('value', '')
                if any(malicious in ip for malicious in ['185.220', '91.219', '45.227']):
                    indicators.append(f'A record points to known malicious IP: {ip}')
            if record['type'] == 'TXT' and '-all' in record.get('value', ''):
                indicators.append('SPF record rejects all email (potential phishing)')
        if not indicators:
            indicators.append('DNS records match patterns of malicious infrastructure')
        return indicators
    
    def reverse_dns_lookup(self, ip: str) -> Optional[str]:
        """
        Simulate reverse DNS lookup for an IP address
        
        Returns hostname if found
        """
        # Check cache first
        cached = self._get_cached_data('reverse_dns', ip)
        if cached:
            return cached.get('hostname')
        
        # Generate reverse DNS
        hostname = self._generate_reverse_dns(ip)
        
        if hostname:
            self._cache_data('reverse_dns', ip, {'hostname': hostname})
        
        return hostname
    
    def _generate_reverse_dns(self, ip: str) -> Optional[str]:
        """Generate realistic reverse DNS"""
        try:
            ip_obj = ip_address(ip)
            if ip_obj.is_private:
                return None
        except ValueError:
            pass
        
        # Generate based on IP patterns
        if ip.startswith('185.220.'):
            return f'tor-exit-{ip.split(".")[2]}.torproxy.net'
        elif ip.startswith('8.8.'):
            return 'dns.google'
        elif ip.startswith('1.1.'):
            return 'one.one.one.one'
        else:
            return f'{ip.replace(".", "-")}.unknown.domain'
    
    def shodan_lookup(self, ip: str) -> Dict[str, Any]:
        """
        Simulate Shodan API lookup for an IP address
        
        Returns realistic Shodan data for training purposes
        """
        # Check cache first
        cached = self._get_cached_data('shodan', ip)
        if cached:
            return cached
        
        # Generate Shodan data
        data = self._generate_shodan(ip)
        
        # Cache the result
        self._cache_data('shodan', ip, data)
        
        return data
    
    def _generate_shodan(self, ip: str) -> Dict[str, Any]:
        """Generate realistic Shodan data"""
        try:
            ip_obj = ip_address(ip)
            if ip_obj.is_private:
                return {
                    'ip': ip,
                    'error': 'Private IP - no Shodan data available',
                    'is_private': True,
                }
        except ValueError:
            pass
        
        # Determine if IP has services
        has_ssh = random.random() > 0.3
        has_http = random.random() > 0.4
        has_telnet = random.random() > 0.8
        has_ftp = random.random() > 0.7
        
        ports = []
        if has_ssh:
            ports.append(22)
        if has_http:
            ports.append(80)
        if has_telnet:
            ports.append(23)
        if has_ftp:
            ports.append(21)
        
        vulns = []
        if random.random() > 0.7:
            vulns = ['CVE-2024-1234', 'CVE-2023-5678']
        
        return {
            'ip': ip,
            'ports': ports,
            'hostnames': [self._generate_reverse_dns(ip)] if self._generate_reverse_dns(ip) else [],
            'country': self._get_country_by_ip(ip),
            'org': self.ISP_DATA.get(ip, {}).get('org', 'Unknown'),
            'os': f'Linux {random.choice([3, 4, 5])}.x',
            'vulnerabilities': vulns,
            'vuln_count': len(vulns),
            'last_update': datetime.utcnow().isoformat(),
            'is_malicious': self._is_known_malicious_ip(ip),
            'threat_score': random.randint(50, 100) if self._is_known_malicious_ip(ip) else random.randint(0, 30),
        }
    
    def _get_country_by_ip(self, ip: str) -> str:
        """Get country code based on IP"""
        ip_hash = hash(ip)
        country_codes = list(self.COUNTRIES.keys())
        return self.COUNTRIES[country_codes[ip_hash % len(country_codes)]]['code']
    
    def _get_cached_data(self, query_type: str, query_value: str) -> Optional[Dict]:
        """Get data from cache"""
        if not self.db:
            return None
        
        try:
            result = self.db.execute(
                """SELECT result_data FROM enriched_data_cache 
                WHERE query_type = :type AND query_value = :value 
                AND expires_at > NOW()""",
                {"type": query_type, "value": query_value}
            )
            row = result.fetchone()
            if row and row.get('result_data'):
                if isinstance(row['result_data'], str):
                    return json.loads(row['result_data'])
                return row['result_data']
        except Exception as e:
            print(f"Error getting cached data: {e}")
        return None
    
    def _cache_data(self, query_type: str, query_value: str, data: Dict):
        """Cache enriched data"""
        if not self.db:
            return
        
        try:
            self.db.execute(
                """INSERT INTO enriched_data_cache 
                (query_type, query_value, result_data, expires_at, source)
                VALUES (:type, :value, :data, :expires, :source)
                ON CONFLICT (query_type, query_value)
                DO UPDATE SET result_data = :data, expires_at = :expires""",
                {
                    "type": query_type,
                    "value": query_value,
                    "data": json.dumps(data),
                    "expires": datetime.utcnow() + self.cache_duration,
                    "source": "simulation",
                }
            )
            self.db.commit()
        except Exception as e:
            print(f"Error caching data: {e}")
    
    def enrich_artifact(self, artifact_type: str, value: str) -> Dict[str, Any]:
        """
        Enrich an artifact with available data
        
        Returns comprehensive enrichment data based on artifact type
        """
        result = {
            'type': artifact_type,
            'value': value,
            'enrichment': {},
            'threat_indicators': [],
            'enriched_at': datetime.utcnow().isoformat(),
        }
        
        if artifact_type == 'ip':
            result['enrichment']['geolocation'] = self.geolocation_lookup(value)
            result['enrichment']['reverse_dns'] = self.reverse_dns_lookup(value)
            result['enrichment']['shodan'] = self.shodan_lookup(value)
            
            # Check for threat indicators
            geo = result['enrichment']['geolocation']
            if geo.get('is_malicious'):
                result['threat_indicators'].append('IP is in known malicious range')
                result['threat_indicators'].append(f"Abuse confidence score: {geo.get('abuse_confidence_score', 0)}")
            
        elif artifact_type == 'domain':
            result['enrichment']['whois'] = self.whois_lookup(value)
            result['enrichment']['pdns'] = self.pdns_lookup(value)
            
            # Check for threat indicators
            whois = result['enrichment'].get('whois', {})
            if whois.get('is_suspicious'):
                result['threat_indicators'].extend(whois.get('threat_indicators', []))
            
            pdns = result['enrichment'].get('pdns', {})
            if pdns.get('is_suspicious'):
                result['threat_indicators'].extend(pdns.get('threat_indicators', []))
        
        elif artifact_type == 'url':
            # Extract domain from URL
            domain_match = re.search(r'https?://([^/]+)', value)
            if domain_match:
                domain = domain_match.group(1)
                result['enrichment']['domain'] = self.whois_lookup(domain)
                result['enrichment']['pdns'] = self.pdns_lookup(domain)
        
        return result
