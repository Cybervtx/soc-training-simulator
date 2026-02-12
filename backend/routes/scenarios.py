"""
Scenario Routes - SOC Training Simulator (Parte 2)
API endpoints for scenarios, artifacts, and timeline
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session
import sys
sys.path.insert(0, '/workspaces/soc-training-simulator')

from backend.config import get_config
from backend.services.scenario_generator_service import ScenarioGeneratorService
from backend.models.scenario import (
    Scenario, ScenarioArtifact, ScenarioTimelineEvent, UserInvestigationProgress,
    InvestigationNote, ArtifactTypes, DifficultyLevels, IncidentTypes
)


# Create blueprint
scenarios_bp = Blueprint('scenarios', __name__, url_prefix='/api/scenarios')

# Service instances
scenario_service = ScenarioGeneratorService()


@scenarios_bp.route('', methods=['GET'])
def list_scenarios():
    """List all available scenarios"""
    try:
        scenarios = scenario_service.get_available_scenarios()
        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in scenarios],
            'count': len(scenarios)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/<scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    """Get a specific scenario with artifacts and timeline"""
    try:
        scenario_uuid = uuid.UUID(scenario_id)
        scenario = scenario_service.get_scenario_by_id(scenario_uuid)
        
        if not scenario:
            return jsonify({
                'success': False,
                'error': 'Scenario not found'
            }), 404
        
        # Get artifacts and timeline
        artifacts = scenario_service.get_artifacts_by_scenario(scenario_uuid)
        timeline = scenario_service.get_timeline_by_scenario(scenario_uuid)
        
        return jsonify({
            'success': True,
            'data': {
                'scenario': scenario.to_dict(),
                'artifacts': [a.to_dict() for a in artifacts],
                'timeline': [t.to_dict() for t in timeline],
                'learning_objectives': scenario.learning_objectives
            }
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid scenario ID format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/generate', methods=['POST'])
def generate_scenario():
    """Generate a new scenario from template"""
    try:
        data = request.get_json() or {}
        incident_type = data.get('incident_type', IncidentTypes.PORT_SCANNING)
        difficulty = data.get('difficulty', DifficultyLevels.BEGINNER)
        
        # Get template by type
        template = scenario_service.get_template_by_type(incident_type)
        
        if not template:
            return jsonify({
                'success': False,
                'error': f'No template found for incident type: {incident_type}',
                'available_types': [t.value for t in IncidentTypes]
            }), 404
        
        # Generate scenario
        scenario = scenario_service.generate_scenario(template, difficulty)
        artifacts = scenario_service.generate_artifacts(scenario.id, template, difficulty)
        timeline = scenario_service.generate_timeline(scenario.id, template, artifacts, difficulty)
        
        # Save to database
        scenario_service.save_scenario_to_db(scenario, artifacts, timeline)
        
        return jsonify({
            'success': True,
            'data': {
                'scenario': scenario.to_dict(),
                'artifacts': [a.to_dict() for a in artifacts],
                'timeline': [t.to_dict() for t in timeline]
            }
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/<scenario_id>/artifacts', methods=['GET'])
def get_artifacts(scenario_id):
    """Get all artifacts for a scenario"""
    try:
        scenario_uuid = uuid.UUID(scenario_id)
        artifacts = scenario_service.get_artifacts_by_scenario(scenario_uuid)
        
        return jsonify({
            'success': True,
            'data': [a.to_dict() for a in artifacts],
            'count': len(artifacts)
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid scenario ID format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/<scenario_id>/timeline', methods=['GET'])
def get_timeline(scenario_id):
    """Get timeline events for a scenario"""
    try:
        scenario_uuid = uuid.UUID(scenario_id)
        events = scenario_service.get_timeline_by_scenario(scenario_uuid)
        
        # Group by date for easier display
        events_by_date = {}
        for event in events:
            date_key = event.timestamp.strftime('%Y-%m-%d')
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event.to_dict())
        
        return jsonify({
            'success': True,
            'data': events_by_date,
            'events': [e.to_dict() for e in events],
            'count': len(events)
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid scenario ID format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/templates', methods=['GET'])
def list_templates():
    """List available scenario templates"""
    try:
        from flask import g
        config = get_config()
        
        templates = [
            {
                'id': str(t.value),
                'name': t.name,
                'description': IncidentTypes.__dict__.get(t.value, {}).get('__doc__', ''),
                'types': list(IncidentTypes.__dict__.keys())
            }
            for t in IncidentTypes
        ]
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'id': IncidentTypes.PORT_SCANNING,
                    'name': 'Port Scanning',
                    'description': 'Detect and investigate port scanning activity',
                    'difficulty_levels': list(DifficultyLevels.__dict__.keys())
                },
                {
                    'id': IncidentTypes.BRUTE_FORCE,
                    'name': 'Brute Force Attack',
                    'description': 'Investigate brute force authentication attempts',
                    'difficulty_levels': list(DifficultyLevels.__dict__.keys())
                },
                {
                    'id': IncidentTypes.C2_COMMUNICATION,
                    'name': 'C2 Communication',
                    'description': 'Detect and analyze command and control traffic',
                    'difficulty_levels': list(DifficultyLevels.__dict__.keys())
                },
                {
                    'id': IncidentTypes.MALWARE_DISTRIBUTION,
                    'name': 'Malware Distribution',
                    'description': 'Investigate malware distribution campaigns',
                    'difficulty_levels': list(DifficultyLevels.__dict__.keys())
                },
                {
                    'id': IncidentTypes.PHISHING_CAMPAIGN,
                    'name': 'Phishing Campaign',
                    'description': 'Analyze phishing email campaigns',
                    'difficulty_levels': list(DifficultyLevels.__dict__.keys())
                },
                {
                    'id': IncidentTypes.DATA_EXFILTRATION,
                    'name': 'Data Exfiltration',
                    'description': 'Investigate data exfiltration attempts',
                    'difficulty_levels': list(DifficultyLevels.__dict__.keys())
                },
                {
                    'id': IncidentTypes.APT_ACTIVITY,
                    'name': 'APT Activity',
                    'description': 'Investigate advanced persistent threat activity',
                    'difficulty_levels': list(DifficultyLevels.__dict__.keys())
                }
            ]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/<scenario_id>/start', methods=['POST'])
def start_investigation(scenario_id):
    """Start an investigation for a scenario"""
    try:
        from flask import g
        
        scenario_uuid = uuid.UUID(scenario_id)
        user_id = session.get('user_id')
        
        if not user_id:
            # For demo purposes, use a default user
            user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        
        # Check if investigation already exists
        from backend.config import get_db
        db = get_db()
        
        result = db.execute(
            """SELECT * FROM user_investigation_progress 
            WHERE scenario_id = :scenario_id AND user_id = :user_id""",
            {'scenario_id': scenario_uuid, 'user_id': user_id}
        )
        existing = result.fetchone()
        
        if existing:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Investigation already in progress',
                    'progress': existing
                }
            }), 200
        
        # Create new investigation progress
        progress = UserInvestigationProgress(
            id=uuid.uuid4(),
            scenario_id=scenario_uuid,
            user_id=user_id,
            status='in_progress',
            started_at=datetime.utcnow()
        )
        
        db.execute(
            """INSERT INTO user_investigation_progress 
            (id, scenario_id, user_id, status, started_at)
            VALUES (:id, :scenario_id, :user_id, :status, :started_at)""",
            {
                'id': progress.id,
                'scenario_id': progress.scenario_id,
                'user_id': progress.user_id,
                'status': progress.status,
                'started_at': progress.started_at
            }
        )
        db.commit()
        
        return jsonify({
            'success': True,
            'data': progress.to_dict()
        }), 201
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid scenario ID format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/<scenario_id>/submit', methods=['POST'])
def submit_investigation(scenario_id):
    """Submit an investigation with conclusions and recommendations"""
    try:
        from flask import g, session
        
        scenario_uuid = uuid.UUID(scenario_id)
        data = request.get_json() or {}
        user_id = session.get('user_id')
        
        if not user_id:
            user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        
        conclusions = data.get('conclusions', '')
        recommendations = data.get('recommendations', '')
        notes = data.get('notes', [])
        
        from backend.config import get_db
        db = get_db()
        
        # Update investigation progress
        db.execute(
            """UPDATE user_investigation_progress 
            SET status = 'submitted', 
                completed_at = :completed_at,
                conclusions = :conclusions,
                recommendations = :recommendations,
                updated_at = :updated_at
            WHERE scenario_id = :scenario_id AND user_id = :user_id""",
            {
                'scenario_id': scenario_uuid,
                'user_id': user_id,
                'completed_at': datetime.utcnow(),
                'conclusions': conclusions,
                'recommendations': recommendations,
                'updated_at': datetime.utcnow()
            }
        )
        
        # Save investigation notes
        for note_data in notes:
            note = InvestigationNote(
                id=uuid.uuid4(),
                scenario_id=scenario_uuid,
                user_id=user_id,
                artifact_id=uuid.UUID(note_data.get('artifact_id')) if note_data.get('artifact_id') else None,
                content=note_data.get('content', ''),
                tags=note_data.get('tags', [])
            )
            db.execute(
                """INSERT INTO investigation_notes 
                (id, scenario_id, user_id, artifact_id, content, tags)
                VALUES (:id, :scenario_id, :user_id, :artifact_id, :content, :tags)""",
                {
                    'id': note.id,
                    'scenario_id': note.scenario_id,
                    'user_id': note.user_id,
                    'artifact_id': note.artifact_id,
                    'content': note.content,
                    'tags': note.tags
                }
            )
        
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Investigation submitted successfully',
                'status': 'submitted',
                'completed_at': datetime.utcnow().isoformat()
            }
        }), 200
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid scenario ID format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scenarios_bp.route('/<scenario_id>/notes', methods=['GET', 'POST'])
def manage_notes(scenario_id):
    """Get or create investigation notes"""
    try:
        from flask import g, session
        
        scenario_uuid = uuid.UUID(scenario_id)
        user_id = session.get('user_id')
        
        if not user_id:
            user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        
        from backend.config import get_db
        db = get_db()
        
        if request.method == 'GET':
            result = db.execute(
                """SELECT * FROM investigation_notes 
                WHERE scenario_id = :scenario_id AND user_id = :user_id
                ORDER BY created_at DESC""",
                {'scenario_id': scenario_uuid, 'user_id': user_id}
            )
            notes = []
            for row in result.fetchall():
                notes.append({
                    'id': str(row['id']),
                    'scenario_id': str(row['scenario_id']),
                    'user_id': str(row['user_id']),
                    'artifact_id': str(row['artifact_id']) if row['artifact_id'] else None,
                    'content': row['content'],
                    'tags': row['tags'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return jsonify({
                'success': True,
                'data': notes,
                'count': len(notes)
            }), 200
        
        else:  # POST
            data = request.get_json() or {}
            
            note = InvestigationNote(
                id=uuid.uuid4(),
                scenario_id=scenario_uuid,
                user_id=user_id,
                artifact_id=uuid.UUID(data.get('artifact_id')) if data.get('artifact_id') else None,
                content=data.get('content', ''),
                tags=data.get('tags', [])
            )
            
            db.execute(
                """INSERT INTO investigation_notes 
                (id, scenario_id, user_id, artifact_id, content, tags)
                VALUES (:id, :scenario_id, :user_id, :artifact_id, :content, :tags)""",
                {
                    'id': note.id,
                    'scenario_id': note.scenario_id,
                    'user_id': note.user_id,
                    'artifact_id': note.artifact_id,
                    'content': note.content,
                    'tags': note.tags
                }
            )
            db.commit()
            
            return jsonify({
                'success': True,
                'data': note.to_dict()
            }), 201
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid scenario ID format'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
