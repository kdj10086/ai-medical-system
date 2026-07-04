from flask import Blueprint, request, jsonify
from models import db, Consultation
from services.llm_service import chat as llm_chat, chat_stream as llm_chat_stream
from routes.auth import token_required
from routes.settings import get_user_llm_config
import json
import uuid
from flask import Response

consultation_bp = Blueprint('consultation', __name__)


@consultation_bp.route('/chat', methods=['POST'])
@token_required
def chat():
    """Handle a consultation chat turn."""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    # Use `or` (not get's default) so an empty-string session_id also
    # generates a fresh id — otherwise every new consultation collapses
    # into a single blank session_id.
    session_id = (data.get('session_id') or '').strip() or str(uuid.uuid4())[:12]

    if not user_message:
        return jsonify({'error': '消息不能为空'}), 400

    # Save user message
    user_msg = Consultation(
        user_id=request.user_id,
        session_id=session_id,
        role='user',
        message=user_message
    )
    db.session.add(user_msg)

    # Get conversation history for this session
    history = Consultation.query.filter_by(
        user_id=request.user_id,
        session_id=session_id
    ).order_by(Consultation.created_at.asc()).all()

    history_list = [{'role': h.role, 'content': h.message} for h in history]

    # Get user's LLM config (if any)
    llm_config = get_user_llm_config(request.user_id)

    # Get AI response
    ai_response = llm_chat(user_message, history_list, config=llm_config)

    # Save AI response
    ai_msg = Consultation(
        user_id=request.user_id,
        session_id=session_id,
        role='assistant',
        message=ai_response
    )
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({
        'session_id': session_id,
        'user_message': user_message,
        'assistant_message': ai_response,
        'symptom_summary_detected': '【症状总结】' in ai_response
    })


@consultation_bp.route('/chat/stream', methods=['POST'])
@token_required
def chat_stream():
    """SSE streaming version of the chat endpoint for real-time AI output."""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = (data.get('session_id') or '').strip() or str(uuid.uuid4())[:12]

    if not user_message:
        return jsonify({'error': '消息不能为空'}), 400

    # Save user message AND commit before streaming so DB is queryable
    # immediately (e.g. delete/history requests arriving mid-stream).
    user_msg = Consultation(
        user_id=request.user_id,
        session_id=session_id,
        role='user',
        message=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    # Get conversation history
    history = Consultation.query.filter_by(
        user_id=request.user_id,
        session_id=session_id
    ).order_by(Consultation.created_at.asc()).all()
    history_list = [{'role': h.role, 'content': h.message} for h in history]

    llm_config = get_user_llm_config(request.user_id)

    def generate():
        """SSE event stream — yields chunks until done, then sends a final
        [DONE] marker and saves the full response to DB."""
        full_response = ""
        try:
            for chunk in llm_chat_stream(user_message, history_list, config=llm_config):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        # Save assistant response to DB
        try:
            ai_msg = Consultation(
                user_id=request.user_id,
                session_id=session_id,
                role='assistant',
                message=full_response
            )
            db.session.add(ai_msg)
            db.session.commit()
        except Exception as e:
            print(f"DB save error in stream: {e}")

        # Send final marker with metadata
        yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'symptom_summary_detected': '【症状总结】' in full_response})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',   # disable nginx buffering
            'Connection': 'keep-alive',
        }
    )


@consultation_bp.route('/history', methods=['GET'])
@token_required
def history():
    """Get consultation history for the current user."""
    sessions = db.session.query(
        Consultation.session_id,
        db.func.min(Consultation.created_at).label('started_at'),
        db.func.count(Consultation.id).label('message_count')
    ).filter_by(user_id=request.user_id)\
     .group_by(Consultation.session_id)\
     .order_by(db.func.min(Consultation.created_at).desc())\
     .all()

    result = []
    for s in sessions:
        result.append({
            'session_id': s.session_id,
            'started_at': s.started_at.isoformat() if s.started_at else None,
            'message_count': s.message_count
        })

    return jsonify({'sessions': result})


@consultation_bp.route('/session/<session_id>', methods=['GET'])
@token_required
def get_session(session_id):
    """Get all messages for a specific consultation session."""
    messages = Consultation.query.filter_by(
        user_id=request.user_id,
        session_id=session_id
    ).order_by(Consultation.created_at.asc()).all()

    return jsonify({
        'session_id': session_id,
        'messages': [m.to_dict() for m in messages]
    })


@consultation_bp.route('/session/<session_id>', methods=['DELETE'])
@token_required
def delete_session(session_id):
    """Delete an entire consultation session (all its messages)."""
    deleted = Consultation.query.filter_by(
        user_id=request.user_id,
        session_id=session_id
    ).delete()
    db.session.commit()

    if not deleted:
        return jsonify({'error': '会话不存在'}), 404
    return jsonify({'message': '会话已删除', 'deleted': deleted})
