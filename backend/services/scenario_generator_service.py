"""
Scenario Generator Service - SOC Training Simulator (Parte 2)
Service for generating realistic training scenarios based on templates and real data
"""

import uuid
import random
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import sys
sys.path.insert(0, '/workspaces/soc-training-simulator')

from backend.config import get_config
from backend.models.scenario import (
    Scenario, ScenarioArtifact, ScenarioTimelineEvent, ScenarioTemplate,
    EventTypes, ArtifactTypes, DifficultyLevels, IncidentTypes
)


class ScenarioGeneratorService:
    """Service for generating training scenarios"""
    
    # Realistic malicious IPs from historical AbuseIPDB data
    MALICIOUS_IPS = [
        "185.220.101.42",  # German VPN/Tor exit node
        "91.219.236.166",  # Russian malicious IP
        "45.227.254.12",   # Brazilian malicious IP
        "103.35.74.21",    # Asian malicious IP
        "212.83.178.156",  # French malicious IP
        "185.234.72.14",   # Ukrainian malicious IP
        "89.248.168.212",  # Dutch scanner
        "195.154.60.193",  # French malicious IP
        "91.207.174.23",   # Russian malicious IP
        "45.154.255.147",  # US malicious IP
    ]
    
    # Benign IPs for noise/legitimate traffic
    BENIGN_IPS = [
        "8.8.8.8",         # Google DNS
        "1.1.1.1",         # Cloudflare DNS
        "208.67.222.222",  # OpenDNS
        "10.0.0.1",        # Private gateway
        "192.168.1.1",     # Private router
    ]
    
    # Malicious domains for scenarios
    MALICIOUS_DOMAINS = [
        "malware-c2.badssl.com",
        "phishing-test.example.com",
        "brute-force.badssl.com",
        "scanner.badssl.com",
        "exfil-test.evil.com",
        "apt-c2.secure-apt.net",
    ]
    
    # Target IPs for internal network
    TARGET_IPS = [
        "10.0.0.5",
        "10.0.0.10",
        "10.0.0.15",
        "192.168.1.100",
        "172.16.0.50",
    ]
    
    def __init__(self, db_session=None):
        self.db = db_session
        self.config = get_config()
    
    def get_template_by_type(self, incident_type: str) -> Optional[ScenarioTemplate]:
        """Get a random template by incident type"""
        if not self.db:
            return None
        
        try:
            result = self.db.execute(
                "SELECT * FROM scenario_templates WHERE incident_type = :type AND is_active = true",
                {"type": incident_type}
            )
            row = result.fetchone()
            if row:
                return self._row_to_template(row)
            return None
        except Exception as e:
            print(f"Error getting template: {e}")
            return None
    
    def _row_to_template(self, row) -> ScenarioTemplate:
        """Convert database row to ScenarioTemplate"""
        base_timeline = row.get('base_timeline', [])
        if isinstance(base_timeline, str):
            base_timeline = json.loads(base_timeline)
        
        base_artifacts = row.get('base_artifacts', [])
        if isinstance(base_artifacts, str):
            base_artifacts = json.loads(base_artifacts)
        
        return ScenarioTemplate(
            id=row['id'],
            name=row['name'],
            incident_type=row['incident_type'],
            description=row['description'],
            base_timeline=base_timeline,
            base_artifacts=base_artifacts,
            default_difficulty=row.get('default_difficulty', 'beginner'),
            estimated_duration=row.get('estimated_duration'),
            created_by=row.get('created_by'),
            created_at=row.get('created_at', datetime.utcnow()),
            is_active=row.get('is_active', True)
        )
    
    def generate_scenario(
        self,
        template: ScenarioTemplate,
        difficulty: str = None,
        use_real_abuseipdb: bool = True
    ) -> Scenario:
        """
        Generate a complete scenario based on template
        
        Args:
            template: ScenarioTemplate to base the scenario on
            difficulty: Difficulty level (easy, medium, hard)
            use_real_abusedb: Whether to use real AbuseIPDB data
            
        Returns:
            Scenario object with artifacts and timeline
        """
        difficulty = difficulty or template.default_difficulty
        
        # Generate scenario basic info
        scenario = Scenario(
            id=uuid.uuid4(),
            title=self._generate_title(template),
            description=self._generate_description(template),
            difficulty=difficulty,
            estimated_duration=template.estimated_duration or self._estimate_duration(difficulty),
            created_by=template.created_by,
            incident_type=template.incident_type,
            learning_objectives=self._generate_learning_objectives(template),
            prerequisites=[]
        )
        
        return scenario
    
    def _generate_title(self, template: ScenarioTemplate) -> str:
        """Generate a realistic scenario title"""
        titles = {
            IncidentTypes.PORT_SCANNING: [
                "Reconnaissance Activity Detected",
                "Port Scanning Investigation",
                "Network Scanning Incident Analysis",
            ],
            IncidentTypes.BRUTE_FORCE: [
                "Brute Force Attack Investigation",
                "SSH Credential Brute Force",
                "Unauthorized Access Attempt Analysis",
            ],
            IncidentTypes.C2_COMMUNICATION: [
                "Suspicious C2 Communication Detected",
                "Beacon Pattern Analysis",
                "Command and Control Traffic Investigation",
            ],
            IncidentTypes.MALWARE_DISTRIBUTION: [
                "Malware Distribution Incident",
                "Suspicious File Download Analysis",
                "Malware Infection Investigation",
            ],
            IncidentTypes.PHISHING_CAMPAIGN: [
                "Phishing Campaign Analysis",
                "Email Phishing Investigation",
                "Malicious Link Analysis",
            ],
            IncidentTypes.DATA_EXFILTRATION: [
                "Data Exfiltration Attempt",
                "Suspicious Data Transfer Investigation",
                "Unauthorized Data Exfil Analysis",
            ],
            IncidentTypes.APT_ACTIVITY: [
                "Advanced Persistent Threat Activity",
                "Sophisticated Attack Investigation",
                "APT Campaign Analysis",
            ],
        }
        
        type_titles = titles.get(template.incident_type, ["Security Incident Investigation"])
        return random.choice(type_titles)
    
    def _generate_description(self, template: ScenarioTemplate) -> str:
        """Generate a scenario description"""
        descriptions = {
            IncidentTypes.PORT_SCANNING: (
                "Our network monitoring systems detected suspicious port scanning activity "
                "originating from an external IP address. Analyze the logs, identify the scanning "
                "patterns, and determine if this is malicious reconnaissance or legitimate activity. "
                "Provide recommendations for mitigation."
            ),
            IncidentTypes.BRUTE_FORCE: (
                "Multiple failed SSH login attempts were detected from a single external IP address. "
                "The attack pattern suggests a brute force attempt to gain unauthorized access. "
                "Investigate the source, determine if any accounts were compromised, "
                "and recommend appropriate countermeasures."
            ),
            IncidentTypes.C2_COMMUNICATION: (
                "Network traffic analysis detected periodic beacon-like connections to an external "
                "domain that matches known C2 patterns. Investigate the communication, identify any "
                "infected hosts, and analyze the data exfiltration potential."
            ),
            IncidentTypes.MALWARE_DISTRIBUTION: (
                "Security alerts indicate that multiple workstations downloaded executable files "
                "from suspicious URLs. Analyze the files, trace the infection vector, "
                "and identify the malware family and potential impact."
            ),
            IncidentTypes.PHISHING_CAMPAIGN: (
                "Multiple users reported receiving phishing emails with links to credential harvesting "
                "sites. Analyze the emails, trace the origin, identify compromised assets, "
                "and recommend remediation steps."
            ),
            IncidentTypes.DATA_EXFILTRATION: (
                "Unusual large data transfers were detected during off-hours from a production server "
                "to an external IP. Investigate the data transfer, determine what data was exfiltrated, "
                "and identify the exfiltration method."
            ),
            IncidentTypes.APT_ACTIVITY: (
                "Multiple security indicators suggest possible APT activity targeting our organization. "
                "Correlate the indicators, identify the attack chain, and assess the scope of compromise."
            ),
        }
        
        return descriptions.get(template.incident_type, template.description or "")
    
    def _estimate_duration(self, difficulty: str) -> int:
        """Estimate scenario duration based on difficulty"""
        durations = {
            DifficultyLevels.BEGINNER: 30,
            DifficultyLevels.INTERMEDIATE: 45,
            DifficultyLevels.ADVANCED: 60,
        }
        return durations.get(difficulty, 30)
    
    def _generate_learning_objectives(self, template: ScenarioTemplate) -> List[str]:
        """Generate learning objectives based on incident type"""
        objectives = {
            IncidentTypes.PORT_SCANNING: [
                "Identify port scanning patterns in network logs",
                "Differentiate between reconnaissance and active attacks",
                "Trace attack source using log analysis",
                "Recommend network segmentation strategies"
            ],
            IncidentTypes.BRUTE_FORCE: [
                "Detect brute force attack patterns in authentication logs",
                "Analyze failed login attempts and identify attack vectors",
                "Implement account lockout and rate limiting strategies",
                "Review and strengthen password policies"
            ],
            IncidentTypes.C2_COMMUNICATION: [
                "Identify beaconing patterns in network traffic",
                "Analyze DNS queries for C2 indicators",
                "Correlate network and host-based indicators",
                "Develop detection rules for C2 communication"
            ],
            IncidentTypes.MALWARE_DISTRIBUTION: [
                "Analyze malware delivery mechanisms",
                "Identify indicators of compromise (IoCs)",
                "Trace malware infection vectors",
                "Develop incident response procedures"
            ],
            IncidentTypes.PHISHING_CAMPAIGN: [
                "Analyze phishing email headers and content",
                "Identify phishing indicators and techniques",
                "Trace email delivery path",
                "Implement email security controls"
            ],
            IncidentTypes.DATA_EXFILTRATION: [
                "Identify data exfiltration techniques",
                "Analyze network traffic for anomalies",
                "Implement data loss prevention strategies",
                "Conduct forensic analysis of compromised systems"
            ],
            IncidentTypes.APT_ACTIVITY: [
                "Correlate multiple security indicators",
                "Identify advanced attack techniques",
                "Map attacker tactics and procedures",
                "Develop comprehensive incident response"
            ],
        }
        
        return objectives.get(template.incident_type, ["Investigate the security incident"])
    
    def generate_artifacts(
        self,
        scenario_id: uuid.UUID,
        template: ScenarioTemplate,
        difficulty: str
    ) -> List[ScenarioArtifact]:
        """Generate artifacts for a scenario"""
        artifacts = []
        
        # Add base artifacts from template
        for base_artifact in template.base_artifacts:
            artifact = ScenarioArtifact(
                id=uuid.uuid4(),
                scenario_id=scenario_id,
                type=base_artifact.get('type', ArtifactTypes.IP),
                value=base_artifact.get('value', ''),
                is_malicious=base_artifact.get('is_malicious', False),
                is_critical=base_artifact.get('is_critical', False),
                metadata=base_artifact.get('metadata', {}),
                points=base_artifact.get('points', 10)
            )
            artifacts.append(artifact)
        
        # Add difficulty-based artifacts
        num_additional = self._get_artifact_count_by_difficulty(difficulty)
        
        for _ in range(num_additional):
            # Add benign/noise artifacts
            if random.random() < 0.3:  # 30% chance of benign artifact
                artifact = ScenarioArtifact(
                    id=uuid.uuid4(),
                    scenario_id=scenario_id,
                    type=ArtifactTypes.IP,
                    value=random.choice(self.BENIGN_IPS),
                    is_malicious=False,
                    is_critical=False,
                    metadata={"type": "benign"},
                    points=5
                )
            else:
                # Add additional malicious artifacts
                artifact = ScenarioArtifact(
                    id=uuid.uuid4(),
                    scenario_id=scenario_id,
                    type=random.choice([
                        ArtifactTypes.IP,
                        ArtifactTypes.DOMAIN,
                        ArtifactTypes.URL
                    ]),
                    value=self._generate_artifact_value(),
                    is_malicious=True,
                    is_critical=random.random() < 0.3,
                    metadata={"type": "malicious"},
                    points=random.randint(10, 25)
                )
            artifacts.append(artifact)
        
        return artifacts
    
    def _get_artifact_count_by_difficulty(self, difficulty: str) -> int:
        """Get number of additional artifacts based on difficulty"""
        counts = {
            DifficultyLevels.BEGINNER: 3,
            DifficultyLevels.INTERMEDIATE: 5,
            DifficultyLevels.ADVANCED: 10,
        }
        return counts.get(difficulty, 3)
    
    def _generate_artifact_value(self) -> str:
        """Generate a random artifact value"""
        if random.random() < 0.5:
            return random.choice(self.MALICIOUS_IPS)
        else:
            return random.choice(self.MALICIOUS_DOMAINS)
    
    def generate_timeline(
        self,
        scenario_id: uuid.UUID,
        template: ScenarioTemplate,
        artifacts: List[ScenarioArtifact],
        difficulty: str
    ) -> List[ScenarioTimelineEvent]:
        """Generate timeline events for a scenario"""
        events = []
        
        # Get malicious IPs from artifacts
        malicious_ips = [a.value for a in artifacts if a.type == ArtifactTypes.IP and a.is_malicious]
        target_ip = random.choice(self.TARGET_IPS)
        
        if not malicious_ips:
            malicious_ips = self.MALICIOUS_IPS[:1]
        
        # Base timeline from template
        base_events = template.base_timeline
        if isinstance(base_events, str):
            base_events = json.loads(base_events)
        
        # Process and expand base events
        base_timestamp = datetime.utcnow() - timedelta(hours=2)
        
        for i, base_event in enumerate(base_events):
            # Add time offset based on event index
            event_time = base_timestamp + timedelta(minutes=i * 5)
            
            # Adjust event based on difficulty
            priority = base_event.get('priority', 2)
            if difficulty == DifficultyLevels.BEGINNER:
                priority = min(priority + 1, 3)  # Higher priority for beginners
            elif difficulty == DifficultyLevels.ADVANCED:
                priority = max(priority - 1, 1)  # Lower priority for advanced
            
            # Generate raw log based on event type
            raw_log = self._generate_raw_log(
                base_event.get('event_type', EventTypes.OTHER),
                malicious_ips[0] if malicious_ips else "185.220.101.42",
                target_ip,
                event_time
            )
            
            event = ScenarioTimelineEvent(
                id=uuid.uuid4(),
                scenario_id=scenario_id,
                timestamp=event_time,
                event_type=base_event.get('event_type', EventTypes.OTHER),
                description=base_event.get('description', ''),
                source_ip=malicious_ips[0] if malicious_ips else None,
                destination_ip=target_ip,
                source_port=random.randint(10000, 65535),
                destination_port=self._get_port_by_event_type(base_event.get('event_type', '')),
                artifact_ids=[str(a.id) for a in artifacts if a.value in (malicious_ips or [])],
                priority=priority,
                raw_log=raw_log
            )
            events.append(event)
        
        # Add noise events for medium and hard difficulties
        if difficulty in [DifficultyLevels.INTERMEDIATE, DifficultyLevels.ADVANCED]:
            noise_events = self._generate_noise_events(
                scenario_id, target_ip, base_timestamp, len(base_events)
            )
            events.extend(noise_events)
        
        # Sort by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        return events
    
    def _generate_raw_log(
        self,
        event_type: str,
        source_ip: str,
        dest_ip: str,
        timestamp: datetime
    ) -> str:
        """Generate realistic raw log entry based on event type"""
        log_formats = {
            EventTypes.NETWORK_SCAN: (
                f"{timestamp.isoformat()}Z DENY TCP {source_ip}:{random.randint(10000, 65535)} "
                f"-> {dest_ip}:{random.choice([22, 80, 443, 8080])}"
            ),
            EventTypes.CONNECTION_ATTEMPT: (
                f"{timestamp.isoformat()}Z DENY TCP {source_ip}:{random.randint(10000, 65535)} "
                f"-> {dest_ip}:22"
            ),
            EventTypes.AUTHENTICATION_FAILURE: (
                f"{timestamp.isoformat()}Z FAILED Password for {random.choice(['root', 'admin', 'ubuntu', 'administrator', 'user'])} "
                f"from {source_ip}"
            ),
            EventTypes.AUTHENTICATION_SUCCESS: (
                f"{timestamp.isoformat()}Z ACCEPT Password for {random.choice(['root', 'admin', 'ubuntu'])} "
                f"from {source_ip}"
            ),
            EventTypes.C2_BEACON: (
                f"{timestamp.isoformat()}Z QUERY A malware-c2.badssl.com -> {source_ip}"
            ),
            EventTypes.FILE_DOWNLOAD: (
                f"{timestamp.isoformat()}Z DOWNLOAD /tmp/{random.choice(['malware.bin', 'payload.exe', 'backdoor.sh'])} "
                f"from {source_ip}"
            ),
        }
        
        return log_formats.get(event_type, f"{timestamp.isoformat()}Z {event_type.upper()} from {source_ip}")
    
    def _get_port_by_event_type(self, event_type: str) -> int:
        """Get typical destination port based on event type"""
        ports = {
            EventTypes.NETWORK_SCAN: 22,
            EventTypes.CONNECTION_ATTEMPT: 22,
            EventTypes.AUTHENTICATION_FAILURE: 22,
            EventTypes.AUTHENTICATION_SUCCESS: 22,
            EventTypes.C2_BEACON: 53,
            EventTypes.FILE_DOWNLOAD: 80,
            EventTypes.DATA_EXFILTRATION: 443,
        }
        return ports.get(event_type, 80)
    
    def _generate_noise_events(
        self,
        scenario_id: uuid.UUID,
        target_ip: str,
        base_timestamp: datetime,
        base_event_count: int
    ) -> List[ScenarioTimelineEvent]:
        """Generate noise events for harder difficulties"""
        events = []
        noise_count = random.randint(3, 8)
        
        for i in range(noise_count):
            event_time = base_timestamp + timedelta(
                minutes=random.randint(0, base_event_count * 5 + 30)
            )
            
            event = ScenarioTimelineEvent(
                id=uuid.uuid4(),
                scenario_id=scenario_id,
                timestamp=event_time,
                event_type=random.choice([
                    EventTypes.CONNECTION_ATTEMPT,
                    EventTypes.NETWORK_SCAN,
                    EventTypes.OTHER
                ]),
                description="Noise event - benign activity",
                source_ip=random.choice(self.BENIGN_IPS),
                destination_ip=target_ip,
                destination_port=random.choice([53, 80, 443]),
                priority=1,
                raw_log=f"{event_time.isoformat()}Z BENIGN traffic from benign IP"
            )
            events.append(event)
        
        return events
    
    def save_scenario_to_db(
        self,
        scenario: Scenario,
        artifacts: List[ScenarioArtifact],
        timeline: List[ScenarioTimelineEvent]
    ) -> bool:
        """Save generated scenario to database"""
        if not self.db:
            return False
        
        try:
            # Save scenario
            self.db.execute(
                """INSERT INTO scenarios 
                (id, title, description, difficulty, estimated_duration, created_by, 
                incident_type, learning_objectives, prerequisites)
                VALUES (:id, :title, :description, :difficulty, :estimated_duration, :created_by,
                :incident_type, :learning_objectives, :prerequisites)""",
                {
                    "id": scenario.id,
                    "title": scenario.title,
                    "description": scenario.description,
                    "difficulty": scenario.difficulty,
                    "estimated_duration": scenario.estimated_duration,
                    "created_by": scenario.created_by,
                    "incident_type": scenario.incident_type,
                    "learning_objectives": json.dumps(scenario.learning_objectives),
                    "prerequisites": json.dumps(scenario.prerequisites)
                }
            )
            
            # Save artifacts
            for artifact in artifacts:
                self.db.execute(
                    """INSERT INTO scenario_artifacts 
                    (id, scenario_id, type, value, is_malicious, is_critical, metadata, points)
                    VALUES (:id, :scenario_id, :type, :value, :is_malicious, :is_critical, :metadata, :points)""",
                    {
                        "id": artifact.id,
                        "scenario_id": artifact.scenario_id,
                        "type": artifact.type,
                        "value": artifact.value,
                        "is_malicious": artifact.is_malicious,
                        "is_critical": artifact.is_critical,
                        "metadata": json.dumps(artifact.metadata),
                        "points": artifact.points
                    }
                )
            
            # Save timeline
            for event in timeline:
                self.db.execute(
                    """INSERT INTO scenario_timeline 
                    (id, scenario_id, timestamp, event_type, description, source_ip, 
                    destination_ip, source_port, destination_port, artifact_ids, priority, raw_log)
                    VALUES (:id, :scenario_id, :timestamp, :event_type, :description, :source_ip,
                    :destination_ip, :source_port, :destination_port, :artifact_ids, :priority, :raw_log)""",
                    {
                        "id": event.id,
                        "scenario_id": event.scenario_id,
                        "timestamp": event.timestamp,
                        "event_type": event.event_type,
                        "description": event.description,
                        "source_ip": event.source_ip,
                        "destination_ip": event.destination_ip,
                        "source_port": event.source_port,
                        "destination_port": event.destination_port,
                        "artifact_ids": json.dumps(event.artifact_ids),
                        "priority": event.priority,
                        "raw_log": event.raw_log
                    }
                )
            
            self.db.commit()
            return True
            
        except Exception as e:
            print(f"Error saving scenario: {e}")
            self.db.rollback()
            return False
    
    def get_scenario_by_id(self, scenario_id: uuid.UUID) -> Optional[Scenario]:
        """Get scenario by ID from database"""
        if not self.db:
            return None
        
        try:
            result = self.db.execute(
                "SELECT * FROM scenarios WHERE id = :id",
                {"id": scenario_id}
            )
            row = result.fetchone()
            if row:
                return self._row_to_scenario(row)
            return None
        except Exception as e:
            print(f"Error getting scenario: {e}")
            return None
    
    def _row_to_scenario(self, row) -> Scenario:
        """Convert database row to Scenario"""
        learning_objectives = row.get('learning_objectives', [])
        if isinstance(learning_objectives, str):
            learning_objectives = json.loads(learning_objectives)
        
        prerequisites = row.get('prerequisites', [])
        if isinstance(prerequisites, str):
            prerequisites = json.loads(prerequisites)
        
        return Scenario(
            id=row['id'],
            title=row['title'],
            description=row.get('description'),
            difficulty=row.get('difficulty', 'beginner'),
            estimated_duration=row.get('estimated_duration'),
            created_by=row.get('created_by'),
            created_at=row.get('created_at', datetime.utcnow()),
            updated_at=row.get('updated_at', datetime.utcnow()),
            is_active=row.get('is_active', True),
            learning_objectives=learning_objectives,
            prerequisites=prerequisites,
            incident_type=row.get('incident_type')
        )
    
    def get_artifacts_by_scenario(self, scenario_id: uuid.UUID) -> List[ScenarioArtifact]:
        """Get all artifacts for a scenario"""
        if not self.db:
            return []
        
        try:
            result = self.db.execute(
                "SELECT * FROM scenario_artifacts WHERE scenario_id = :scenario_id",
                {"scenario_id": scenario_id}
            )
            return [self._row_to_artifact(row) for row in result.fetchall()]
        except Exception as e:
            print(f"Error getting artifacts: {e}")
            return []
    
    def _row_to_artifact(self, row) -> ScenarioArtifact:
        """Convert database row to ScenarioArtifact"""
        metadata = row.get('metadata', {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        return ScenarioArtifact(
            id=row['id'],
            scenario_id=row['scenario_id'],
            type=row['type'],
            value=row['value'],
            is_malicious=row.get('is_malicious', False),
            is_critical=row.get('is_critical', False),
            metadata=metadata,
            points=row.get('points', 10),
            created_at=row.get('created_at', datetime.utcnow())
        )
    
    def get_timeline_by_scenario(self, scenario_id: uuid.UUID) -> List[ScenarioTimelineEvent]:
        """Get all timeline events for a scenario"""
        if not self.db:
            return []
        
        try:
            result = self.db.execute(
                """SELECT * FROM scenario_timeline 
                WHERE scenario_id = :scenario_id 
                ORDER BY timestamp ASC""",
                {"scenario_id": scenario_id}
            )
            return [self._row_to_timeline_event(row) for row in result.fetchall()]
        except Exception as e:
            print(f"Error getting timeline: {e}")
            return []
    
    def _row_to_timeline_event(self, row) -> ScenarioTimelineEvent:
        """Convert database row to ScenarioTimelineEvent"""
        artifact_ids = row.get('artifact_ids', [])
        if isinstance(artifact_ids, str):
            artifact_ids = json.loads(artifact_ids)
        
        return ScenarioTimelineEvent(
            id=row['id'],
            scenario_id=row['scenario_id'],
            timestamp=row['timestamp'],
            event_type=row['event_type'],
            description=row.get('description'),
            source_ip=row.get('source_ip'),
            destination_ip=row.get('destination_ip'),
            source_port=row.get('source_port'),
            destination_port=row.get('destination_port'),
            artifact_ids=artifact_ids,
            priority=row.get('priority', 1),
            raw_log=row.get('raw_log'),
            created_at=row.get('created_at', datetime.utcnow())
        )
    
    def get_available_scenarios(self, user_id: uuid.UUID = None) -> List[Scenario]:
        """Get all available scenarios for users"""
        if not self.db:
            return []
        
        try:
            query = "SELECT * FROM scenarios WHERE is_active = true ORDER BY created_at DESC"
            result = self.db.execute(query)
            return [self._row_to_scenario(row) for row in result.fetchall()]
        except Exception as e:
            print(f"Error getting scenarios: {e}")
            return []
