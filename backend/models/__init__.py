# Database models initialization
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from backend.models.user import User
from backend.models.abuseipdb_cache import AbuseIPDBCache
from backend.models.abuseipdb_log import AbuseIPDBApiLog
from backend.models.scenario import (
    Scenario,
    ScenarioArtifact,
    ScenarioTimelineEvent,
    ScenarioTemplate,
    EnrichedDataCache,
    InvestigationNote,
    UserInvestigationProgress,
    EventTypes,
    ArtifactTypes,
    DifficultyLevels,
    IncidentTypes
)

__all__ = [
    'User', 
    'AbuseIPDBCache', 
    'AbuseIPDBApiLog',
    'Scenario',
    'ScenarioArtifact',
    'ScenarioTimelineEvent',
    'ScenarioTemplate',
    'EnrichedDataCache',
    'InvestigationNote',
    'UserInvestigationProgress',
    'EventTypes',
    'ArtifactTypes',
    'DifficultyLevels',
    'IncidentTypes'
]
