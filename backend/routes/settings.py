from flask import Blueprint, request, jsonify
from models import db, LLMConfig
from routes.auth import token_required

settings_bp = Blueprint('settings', __name__)


def get_user_llm_config(user_id):
    """Helper: get the active LLM config for a user as a dict."""
    config = LLMConfig.query.filter_by(user_id=user_id, is_active=True).first()
    if config and config.api_key:
        return {
            'api_key': config.api_key,
            'base_url': config.base_url,
            'model': config.model
        }
    return None


@settings_bp.route('/llm', methods=['GET'])
@token_required
def get_llm_config():
    """Get current user's LLM configuration."""
    config = LLMConfig.query.filter_by(user_id=request.user_id).first()
    if not config:
        return jsonify({'config': None, 'message': '未配置LLM，当前使用Mock模式'})
    return jsonify({'config': config.to_dict(mask_key=True)})


@settings_bp.route('/llm', methods=['PUT', 'POST'])
@token_required
def save_llm_config():
    """Save or update user's LLM configuration."""
    data = request.get_json()

    api_key = data.get('api_key', '').strip()
    base_url = data.get('base_url', '').strip()
    model = data.get('model', '').strip()
    is_active = data.get('is_active', True)

    if not api_key:
        return jsonify({'error': 'API Key不能为空'}), 400

    config = LLMConfig.query.filter_by(user_id=request.user_id).first()
    if config:
        # Update existing
        config.api_key = api_key
        config.base_url = base_url
        config.model = model
        config.is_active = is_active
    else:
        # Create new
        config = LLMConfig(
            user_id=request.user_id,
            api_key=api_key,
            base_url=base_url,
            model=model,
            is_active=is_active
        )
        db.session.add(config)

    db.session.commit()
    return jsonify({
        'message': 'LLM配置保存成功',
        'config': config.to_dict(mask_key=True)
    })


@settings_bp.route('/llm', methods=['DELETE'])
@token_required
def delete_llm_config():
    """Delete user's LLM configuration."""
    config = LLMConfig.query.filter_by(user_id=request.user_id).first()
    if config:
        db.session.delete(config)
        db.session.commit()
        return jsonify({'message': 'LLM配置已删除，已恢复Mock模式'})
    return jsonify({'message': '无配置需要删除'})


@settings_bp.route('/llm/test', methods=['POST'])
@token_required
def test_llm_connection():
    """Test the LLM connection with current config."""
    data = request.get_json()

    api_key = data.get('api_key', '').strip()
    base_url = data.get('base_url', '').strip()
    model = data.get('model', '').strip()

    if not api_key:
        return jsonify({'error': '请先填写API Key'}), 400

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': '你好，请简单回复"连接成功"'}],
            max_tokens=20
        )
        reply = response.choices[0].message.content
        return jsonify({'success': True, 'message': f'连接成功！模型回复：{reply}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'连接失败：{str(e)}'}), 400
