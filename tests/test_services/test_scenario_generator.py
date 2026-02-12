"""
Tests for Scenario Generator Service - SOC Training Simulator (Parte 2)
"""

import unittest
import uuid
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/workspaces/soc-training-simulator')

from backend.models.scenario import (
    Scenario, ScenarioArtifact, ScenarioTimelineEvent, ScenarioTemplate,
    EventTypes, ArtifactTypes, DifficultyLevels, IncidentTypes
)


class TestScenarioModel(unittest.TestCase):
    """Tests for Scenario model"""
    
    def test_scenario_creation(self):
        """Test creating a Scenario instance"""
        scenario = Scenario(
            id=uuid.uuid4(),
            title="Test Scenario",
            description="Test description",
            difficulty=DifficultyLevels.BEGINNER,
            incident_type=IncidentTypes.PORT_SCANNING,
            learning_objectives=["Objective 1", "Objective 2"]
        )
        
        self.assertEqual(scenario.title, "Test Scenario")
        self.assertEqual(scenario.difficulty, "beginner")
        self.assertEqual(scenario.incident_type, "port_scanning")
        self.assertEqual(len(scenario.learning_objectives), 2)
    
    def test_scenario_to_dict(self):
        """Test Scenario.to_dict() method"""
        scenario = Scenario(
            id=uuid.uuid4(),
            title="Test Scenario",
            description="Test description",
            difficulty=DifficultyLevels.INTERMEDIATE,
            incident_type=IncidentTypes.BRUTE_FORCE
        )
        
        result = scenario.to_dict()
        
        self.assertEqual(result['title'], "Test Scenario")
        self.assertEqual(result['difficulty'], "intermediate")
        self.assertEqual(result['incident_type'], "brute_force")
        self.assertIn('id', result)
        self.assertIn('created_at', result)


class TestScenarioArtifact(unittest.TestCase):
    """Tests for ScenarioArtifact model"""
    
    def test_artifact_creation(self):
        """Test creating a ScenarioArtifact instance"""
        artifact = ScenarioArtifact(
            id=uuid.uuid4(),
            scenario_id=uuid.uuid4(),
            type=ArtifactTypes.IP,
            value="185.220.101.42",
            is_malicious=True,
            is_critical=True,
            points=25
        )
        
        self.assertEqual(artifact.type, "ip")
        self.assertEqual(artifact.value, "185.220.101.42")
        self.assertTrue(artifact.is_malicious)
        self.assertTrue(artifact.is_critical)
        self.assertEqual(artifact.points, 25)
    
    def test_artifact_to_dict(self):
        """Test ScenarioArtifact.to_dict() method"""
        scenario_id = uuid.uuid4()
        artifact = ScenarioArtifact(
            id=uuid.uuid4(),
            scenario_id=scenario_id,
            type=ArtifactTypes.DOMAIN,
            value="malware-c2.badssl.com",
            is_malicious=True,
            metadata={"registrar": "NameCheap"}
        )
        
        result = artifact.to_dict()
        
        self.assertEqual(result['type'], "domain")
        self.assertEqual(result['value'], "malware-c2.badssl.com")
        self.assertTrue(result['is_malicious'])
        self.assertEqual(result['metadata']['registrar'], "NameCheap")


class TestScenarioTimelineEvent(unittest.TestCase):
    """Tests for ScenarioTimelineEvent model"""
    
    def test_event_creation(self):
        """Test creating a ScenarioTimelineEvent instance"""
        event = ScenarioTimelineEvent(
            id=uuid.uuid4(),
            scenario_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            event_type=EventTypes.NETWORK_SCAN,
            description="SYN scan detected",
            source_ip="185.220.101.42",
            destination_ip="10.0.0.5",
            priority=3
        )
        
        self.assertEqual(event.event_type, "network_scan")
        self.assertEqual(event.priority, 3)
        self.assertEqual(event.priority_label, "high")
    
    def test_event_priority_label(self):
        """Test priority_label property"""
        event1 = ScenarioTimelineEvent(
            id=uuid.uuid4(),
            scenario_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            event_type=EventTypes.CONNECTION_ATTEMPT,
            priority=1
        )
        self.assertEqual(event1.priority_label, "low")
        
        event2 = ScenarioTimelineEvent(
            id=uuid.uuid4(),
            scenario_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            event_type=EventTypes.CONNECTION_ATTEMPT,
            priority=2
        )
        self.assertEqual(event2.priority_label, "medium")
        
        event3 = ScenarioTimelineEvent(
            id=uuid.uuid4(),
            scenario_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            event_type=EventTypes.CONNECTION_ATTEMPT,
            priority=3
        )
        self.assertEqual(event3.priority_label, "high")


class TestConstants(unittest.TestCase):
    """Tests for constants"""
    
    def test_event_types(self):
        """Test EventTypes constants"""
        self.assertEqual(EventTypes.NETWORK_SCAN, "network_scan")
        self.assertEqual(EventTypes.AUTHENTICATION_FAILURE, "authentication_failure")
        self.assertEqual(EventTypes.AUTHENTICATION_SUCCESS, "authentication_success")
        self.assertEqual(EventTypes.C2_BEACON, "c2_beacon")
    
    def test_artifact_types(self):
        """Test ArtifactTypes constants"""
        self.assertEqual(ArtifactTypes.IP, "ip")
        self.assertEqual(ArtifactTypes.DOMAIN, "domain")
        self.assertEqual(ArtifactTypes.URL, "url")
        self.assertEqual(ArtifactTypes.FILE_HASH, "file_hash")
    
    def test_difficulty_levels(self):
        """Test DifficultyLevels constants"""
        self.assertEqual(DifficultyLevels.BEGINNER, "beginner")
        self.assertEqual(DifficultyLevels.INTERMEDIATE, "intermediate")
        self.assertEqual(DifficultyLevels.ADVANCED, "advanced")
    
    def test_incident_types(self):
        """Test IncidentTypes constants"""
        self.assertEqual(IncidentTypes.PORT_SCANNING, "port_scanning")
        self.assertEqual(IncidentTypes.BRUTE_FORCE, "brute_force")
        self.assertEqual(IncidentTypes.C2_COMMUNICATION, "c2_communication")


if __name__ == '__main__':
    unittest.main()
