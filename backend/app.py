import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, BASE_DIR
from models import db


def create_app():
    app = Flask(__name__, static_folder=None)

    # Config
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

    # CORS for API (also needed for dev with Vite on :5173)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.consultation import consultation_bp
    from routes.recommendation import recommendation_bp
    from routes.report import report_bp
    from routes.records import records_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(consultation_bp, url_prefix='/api/consultation')
    app.register_blueprint(recommendation_bp, url_prefix='/api/recommendation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(records_bp, url_prefix='/api/records')

    from routes.settings import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'service': 'AI医疗导诊与报告解读系统'}

    # ---- Serve frontend static files (SPA) ----
    # Path to the built frontend: ../frontend/dist
    frontend_dist = os.path.join(BASE_DIR, '..', 'frontend', 'dist')
    frontend_dist = os.path.abspath(frontend_dist)

    if os.path.exists(frontend_dist):
        @app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(frontend_dist, 'assets'), filename)

        @app.route('/')
        @app.route('/<path:path>')
        def serve_frontend(path=''):
            # For SPA: all non-API, non-asset paths serve index.html
            if path.startswith('api/') or path.startswith('assets/'):
                return {'error': 'Not found'}, 404
            return send_from_directory(frontend_dist, 'index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("AI医疗导诊与报告解读系统")
    print("访问地址: http://localhost:5000")
    print("API 地址: http://localhost:5000/api")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
