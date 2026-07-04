import os
import uuid
import json
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from models import db, Report
from services.ocr_service import extract_text
from services.llm_service import interpret_report
from routes.auth import token_required
from routes.settings import get_user_llm_config
from config import UPLOAD_FOLDER

report_bp = Blueprint('report', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@report_bp.route('/upload', methods=['POST'])
@token_required
def upload():
    """Upload a medical report image and get interpretation."""
    if 'file' not in request.files:
        return jsonify({'error': '请选择要上传的文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '请选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'不支持的文件类型，请上传以下格式：{", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Save uploaded file
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    saved_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, saved_filename)
    file.save(filepath)

    # OCR extraction
    try:
        raw_text = extract_text(filepath)
    except Exception as e:
        raw_text = f"OCR识别失败：{str(e)}"

    # LLM interpretation
    try:
        llm_config = get_user_llm_config(request.user_id)
        interpretation, advice, indicators = interpret_report(raw_text, config=llm_config)
    except Exception as e:
        interpretation = f"报告解读失败：{str(e)}"
        advice = ""
        indicators = []

    # Save to database
    report = Report(
        user_id=request.user_id,
        filename=original_filename,
        raw_text=raw_text,
        indicators=json.dumps(indicators, ensure_ascii=False),
        interpretation=interpretation,
        advice=advice
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({
        'message': '报告解读完成',
        'report': report.to_dict()
    }), 201


@report_bp.route('/list', methods=['GET'])
@token_required
def report_list():
    """Get all reports for the current user."""
    reports = Report.query.filter_by(user_id=request.user_id)\
        .order_by(Report.created_at.desc()).all()

    return jsonify({
        'reports': [r.to_dict() for r in reports]
    })


@report_bp.route('/<int:report_id>', methods=['GET'])
@token_required
def report_detail(report_id):
    """Get a specific report detail."""
    report = Report.query.filter_by(id=report_id, user_id=request.user_id).first()
    if not report:
        return jsonify({'error': '报告不存在'}), 404

    return jsonify({'report': report.to_dict()})


@report_bp.route('/<int:report_id>', methods=['DELETE'])
@token_required
def delete_report(report_id):
    """Delete a report and its uploaded file."""
    report = Report.query.filter_by(id=report_id, user_id=request.user_id).first()
    if not report:
        return jsonify({'error': '报告不存在'}), 404

    db.session.delete(report)
    db.session.commit()
    return jsonify({'message': '报告已删除'})
