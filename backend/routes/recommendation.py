from flask import Blueprint, request, jsonify
from models import Consultation, Department
from services.dept_service import recommend_departments, extract_symptoms_from_conversation
from routes.auth import token_required

recommendation_bp = Blueprint('recommendation', __name__)


@recommendation_bp.route('/recommend', methods=['POST'])
@token_required
def recommend():
    """Recommend departments based on symptoms from a consultation session."""
    data = request.get_json()
    session_id = data.get('session_id')
    symptom_text = data.get('symptoms', '').strip()

    # If session_id provided, extract symptoms from that conversation
    if session_id:
        messages = Consultation.query.filter_by(
            user_id=request.user_id,
            session_id=session_id
        ).order_by(Consultation.created_at.asc()).all()

        messages_list = [{'role': m.role, 'content': m.message} for m in messages]
        extracted_text = extract_symptoms_from_conversation(messages_list)
        if extracted_text:
            symptom_text = (symptom_text + ' ' + extracted_text).strip()

    if not symptom_text:
        return jsonify({'error': '请先进行问诊或输入症状描述'}), 400

    results = recommend_departments(symptom_text, top_n=3)

    if not results:
        return jsonify({
            'message': '未能根据当前症状匹配到合适的科室，建议您前往全科门诊或咨询分诊台',
            'recommendations': []
        })

    return jsonify({
        'symptoms_analyzed': symptom_text[:200],
        'recommendations': results
    })


@recommendation_bp.route('/departments', methods=['GET'])
def list_departments():
    """Return all departments (no auth required — static reference data)."""
    depts = Department.query.order_by(Department.category, Department.name).all()
    return jsonify({
        'departments': [d.to_dict() for d in depts],
        'total': len(depts)
    })
