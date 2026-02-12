"""
Scenario Models - SOC Training Simulator (Parte 2)
Models for scenarios, artifacts, timeline, and templates
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class Scenario:
    """Scenario model for training exercises"""
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    difficulty: str = "beginner"
    estimated_duration: Optional[int] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    incident_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "estimated_duration": self.estimated_duration,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "learning_objectives": self.learning_objectives,
            "prerequisites": self.prerequisites,
            "incident_type": self.incident_type
        }


@dataclass
class ScenarioArtifact:
    """Artifact model for scenario evidence"""
    id: uuid.UUID
    scenario_id: uuid.UUID
    type: str  # ip, domain, url, file_hash, email, registry_key, mutex
    value: str
    is_malicious: bool = False
    is_critical: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    points: int = 10
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "scenario_id": str(self.scenario_id),
            "type": self.type,
            "value": self.value,
            "is_malicious": self.is_malicious,
            "is_critical": self.is_critical,
            "metadata": self.metadata,
            "points": self.points,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class ScenarioTimelineEvent:
    """Timeline event model for scenario events"""
    id: uuid.UUID
    scenario_id: uuid.UUID
    timestamp: datetime
    event_type: str
    description: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    artifact_ids: List[str] = field(default_factory=list)
    priority: int = 1  # 1=low, 2=medium, 3=high
    raw_log: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "scenario_id": str(self.scenario_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "description": self.description,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "artifact_ids": self.artifact_ids,
            "priority": self.priority,
            "raw_log": self.raw_log,
            "created_at": self.created_at.isoformat()
        }
    
    @property
    def priority_label(self) -> str:
        labels = {1: "low", 2: "medium", 3: "high"}
        return labels.get(self.priority, "unknown")


@dataclass
class ScenarioTemplate:
    """Scenario template model for generating scenarios"""
    id: uuid.UUID
    name: str
    incident_type: str
    description: Optional[str] = None
    base_timeline: List[Dict[str, Any]] = field(default_factory=list)
    base_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    default_difficulty: str = "beginner"
    estimated_duration: Optional[int] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "incident_type": self.incident_type,
            "description": self.description,
            "base_timeline": self.base_timeline,
            "base_artifacts": self.base_artifacts,
            "default_difficulty": self.default_difficulty,
            "estimated_duration": self.estimated_duration,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }


@dataclass
class EnrichedDataCache:
    """Cache for enriched data (WHOIS, geolocation, pDNS, etc.)"""
    id: Optional[int] = None
    query_type: str  # whois, geolocation, pdns, reverse_dns, shodan, etc
    query_value: str = ""
    result_data: Dict[str, Any] = field(default_factory=dict)
    cached_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query_type": self.query_type,
            "query_value": self.query_value,
            "result_data": self.result_data,
            "cached_at": self.cached_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "source": self.source
        }


@dataclass
class InvestigationNote:
    """User investigation notes"""
    id: uuid.UUID
    scenario_id: uuid.UUID
    user_id: uuid.UUID
    artifact_id: Optional[uuid.UUID] = None
    content: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "scenario_id": str(self.scenario_id),
            "user_id": str(self.user_id),
            "artifact_id": str(self.artifact_id) if self.artifact_id else None,
            "content": self.content,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class UserInvestigationProgress:
    """User progress tracking for investigations"""
    id: uuid.UUID
    scenario_id: uuid.UUID
    user_id: uuid.UUID
    status: str = "in_progress"  # not_started, in_progress, completed, submitted
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    time_spent_seconds: int = 0
    artifacts_reviewed: int = 0
    conclusions: Optional[str] = None
    recommendations: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "scenario_id": str(self.scenario_id),
            "user_id": str(self.user_id),
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "time_spent_seconds": self.time_spent_seconds,
            "artifacts_reviewed": self.artifacts_reviewed,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def add_time(self, seconds: int):
        """Add time spent on investigation"""
        self.time_spent_seconds += seconds
        self.updated_at = datetime.utcnow()
    
    def increment_artifacts_reviewed(self):
        """Increment counter for reviewed artifacts"""
        self.artifacts_reviewed += 1
        self.updated_at = datetime.utcnow()


# Event type constants
class EventTypes:
    """Constants for event types"""
    CONNECTION_ATTEMPT = "connection_attempt"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHENTICATION_SUCCESS = "authentication_success"
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE_DETECTION = "malware_detection"
    NETWORK_SCAN = "network_scan"
    C2_BEACON = "c2_beacon"
    PHISHING_EMAIL = "phishing_email"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PERSISTENCE = "persistence"
    LATERAL_MOVEMENT = "lateral_movement"
    COMMAND_EXECUTION = "command_execution"
    FILE_DOWNLOAD = "file_download"
    REGISTRY_MODIFICATION = "registry_modification"
    SERVICE_INSTALLATION = "service_installation"
    OTHER = "other"


# Artifact type constants
class ArtifactTypes:
    """Constants for artifact types"""
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    REGISTRY_KEY = "registry_key"
    MUTEX = "mutex"


# Difficulty constants
class DifficultyLevels:
    """Constants for difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Incident type constants
class IncidentTypes:
    """Constants for incident types"""
    PORT_SCANNING = "port_scanning"
    BRUTE_FORCE = "brute_force"
    C2_COMMUNICATION = "c2_communication"
    MALWARE_DISTRIBUTION = "malware_distribution"
    PHISHING_CAMPAIGN = "phishing_campaign"
    DATA_EXFILTRATION = "data_exfiltration"
    APT_ACTIVITY = "apt_activity"
