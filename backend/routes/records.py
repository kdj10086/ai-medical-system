from flask import Blueprint, request, jsonify
from models import db, Consultation, Report
from routes.auth import token_required

records_bp = Blueprint('records', __name__)


@records_bp.route('/timeline', methods=['GET'])
@token_required
def timeline():
    """Get a combined timeline of consultations and reports."""
    # Get consultations
    consultations = Consultation.query.filter_by(user_id=request.user_id)\
        .order_by(Consultation.created_at.desc()).limit(50).all()

    # Get reports
    reports = Report.query.filter_by(user_id=request.user_id)\
        .order_by(Report.created_at.desc()).limit(50).all()

    # Build timeline
    timeline_items = []

    for c in consultations:
        preview = c.message[:80] + '...' if len(c.message) > 80 else c.message
        timeline_items.append({
            'type': 'consultation',
            'id': f'c-{c.id}',
            'session_id': c.session_id,
            'role': c.role,
            'preview': preview,
            'full_message': c.message,
            'created_at': c.created_at.isoformat() if c.created_at else None
        })

    for r in reports:
        timeline_items.append({
            'type': 'report',
            'id': f'r-{r.id}',
            'report_id': r.id,
            'filename': r.filename,
            'preview': f"医疗报告：{r.filename}",
            'created_at': r.created_at.isoformat() if r.created_at else None
        })

    # Sort by created_at descending
    timeline_items.sort(key=lambda x: x['created_at'] or '', reverse=True)

    return jsonify({
        'timeline': timeline_items,
        'stats': {
            'consultation_count': db.session.query(
                Consultation.session_id
            ).filter_by(user_id=request.user_id).distinct().count(),
            'report_count': len(reports)
        }
    })
