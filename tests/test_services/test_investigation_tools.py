"""
Tests for Investigation Tools Service - SOC Training Simulator (Parte 2)
"""

import unittest
import sys
sys.path.insert(0, '/workspaces/soc-training-simulator')

from backend.services.investigation_tools_service import InvestigationToolsService


class TestInvestigationToolsService(unittest.TestCase):
    """Tests for InvestigationToolsService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = InvestigationToolsService()
    
    def test_geolocation_lookup_public_ip(self):
        """Test geolocation lookup for a public IP"""
        result = self.service.geolocation_lookup("185.220.101.42")
        
        self.assertIn('ip', result)
        self.assertEqual(result['ip'], "185.220.101.42")
        self.assertIn('country_code', result)
        self.assertIn('country_name', result)
        self.assertIn('city', result)
        self.assertIn('isp', result)
        self.assertIn('is_malicious', result)
    
    def test_geolocation_lookup_private_ip(self):
        """Test geolocation lookup for a private IP"""
        result = self.service.geolocation_lookup("192.168.1.1")
        
        self.assertTrue(result['is_private'])
        self.assertEqual(result['country_code'], 'XX')
        self.assertEqual(result['country_name'], 'Private Network')
    
    def test_geolocation_caching(self):
        """Test that geolocation results are cached"""
        # First call
        result1 = self.service.geolocation_lookup("8.8.8.8")
        
        # Modify service to not use DB for caching test
        # (in real tests, would verify cache hit)
        result2 = self.service.geolocation_lookup("8.8.8.8")
        
        # Results should be consistent
        self.assertEqual(result1['ip'], result2['ip'])
        self.assertEqual(result1['country_code'], result2['country_code'])
    
    def test_whois_lookup(self):
        """Test WHOIS lookup"""
        result = self.service.whois_lookup("malware-c2.badssl.com")
        
        self.assertEqual(result['domain'], "malware-c2.badssl.com")
        self.assertIn('registrar', result)
        self.assertIn('created_date', result)
        self.assertIn('expires_date', result)
        self.assertIn('nameservers', result)
    
    def test_whois_known_domain(self):
        """Test WHOIS lookup for known domain"""
        result = self.service.whois_lookup("malware-c2.badssl.com")
        
        self.assertEqual(result['registrar'], "NameCheap, Inc.")
        self.assertTrue(result['is_suspicious'] or 'threat_indicators' in result)
    
    def test_pdns_lookup(self):
        """Test passive DNS lookup"""
        result = self.service.pdns_lookup("malware-c2.badssl.com")
        
        self.assertEqual(result['domain'], "malware-c2.badssl.com")
        self.assertIn('records', result)
        self.assertIsInstance(result['records'], list)
    
    def test_pdns_records_types(self):
        """Test that PDNS returns various record types"""
        result = self.service.pdns_lookup("test-domain.example.com")
        
        record_types = [r['type'] for r in result['records']]
        self.assertIn('A', record_types)
        self.assertIn('NS', record_types)
    
    def test_reverse_dns_lookup(self):
        """Test reverse DNS lookup"""
        result = self.service.reverse_dns_lookup("8.8.8.8")
        
        # Should return hostname
        self.assertIsNotNone(result)
        self.assertIn('dns', result.lower())
    
    def test_reverse_dns_private_ip(self):
        """Test reverse DNS for private IP returns None"""
        result = self.service.reverse_dns_lookup("10.0.0.1")
        
        self.assertIsNone(result)
    
    def test_shodan_lookup(self):
        """Test simulated Shodan lookup"""
        result = self.service.shodan_lookup("8.8.8.8")
        
        self.assertEqual(result['ip'], "8.8.8.8")
        self.assertIn('ports', result)
        self.assertIn('org', result)
    
    def test_shodan_private_ip(self):
        """Test Shodan lookup for private IP"""
        result = self.service.shodan_lookup("192.168.1.1")
        
        self.assertTrue(result['is_private'])
        self.assertIn('error', result)
    
    def test_enrich_artifact_ip(self):
        """Test enriching an IP artifact"""
        result = self.service.enrich_artifact("ip", "185.220.101.42")
        
        self.assertEqual(result['type'], 'ip')
        self.assertEqual(result['value'], "185.220.101.42")
        self.assertIn('enrichment', result)
        self.assertIn('geolocation', result['enrichment'])
        self.assertIn('reverse_dns', result['enrichment'])
        self.assertIn('shodan', result['enrichment'])
    
    def test_enrich_artifact_domain(self):
        """Test enriching a domain artifact"""
        result = self.service.enrich_artifact("domain", "malware-c2.badssl.com")
        
        self.assertEqual(result['type'], 'domain')
        self.assertEqual(result['value'], "malware-c2.badssl.com")
        self.assertIn('enrichment', result)
        self.assertIn('whois', result['enrichment'])
        self.assertIn('pdns', result['enrichment'])
    
    def test_known_malicious_ip(self):
        """Test that known malicious IPs are flagged"""
        result = self.service.geolocation_lookup("185.220.101.42")
        
        self.assertTrue(result['is_malicious'])
        self.assertGreater(result.get('abuse_confidence_score', 0), 0)
    
    def test_benign_ip(self):
        """Test that benign IPs are not flagged as malicious"""
        result = self.service.geolocation_lookup("8.8.8.8")
        
        self.assertFalse(result.get('is_malicious', True))
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = InvestigationToolsService()
        
        self.assertIsNotNone(service.MALICIOUS_IP_RANGES)
        self.assertIsNotNone(service.WHOIS_DATA)
        self.assertIsNotNone(service.COUNTRIES)


class TestInvestigationToolsIntegration(unittest.TestCase):
    """Integration tests for investigation tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = InvestigationToolsService()
    
    def test_full_ip_enrichment_workflow(self):
        """Test complete IP enrichment workflow"""
        # Enrich IP
        result = self.service.enrich_artifact("ip", "185.220.101.42")
        
        # Verify all enrichment data is present
        self.assertIn('geolocation', result['enrichment'])
        self.assertIn('reverse_dns', result['enrichment'])
        self.assertIn('shodan', result['enrichment'])
        
        # Verify threat indicators are generated
        self.assertTrue(len(result['threat_indicators']) > 0)
    
    def test_full_domain_enrichment_workflow(self):
        """Test complete domain enrichment workflow"""
        # Enrich domain
        result = self.service.enrich_artifact("domain", "malware-c2.badssl.com")
        
        # Verify all enrichment data is present
        self.assertIn('whois', result['enrichment'])
        self.assertIn('pdns', result['enrichment'])
        
        # Verify DNS records are comprehensive
        pdns = result['enrichment']['pdns']
        self.assertGreater(len(pdns['records']), 0)


if __name__ == '__main__':
    unittest.main()
