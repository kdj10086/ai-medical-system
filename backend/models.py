from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class LLMConfig(db.Model):
    __tablename__ = 'llm_configs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    api_key = db.Column(db.String(256), default='')
    base_url = db.Column(db.String(256), default='')
    model = db.Column(db.String(100), default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, mask_key=True):
        d = {
            'id': self.id,
            'base_url': self.base_url,
            'model': self.model,
            'is_active': self.is_active,
            'has_api_key': bool(self.api_key),
        }
        if mask_key and self.api_key:
            d['api_key'] = self.api_key[:4] + '****' + self.api_key[-4:] if len(self.api_key) > 8 else '****'
        elif not mask_key:
            d['api_key'] = self.api_key
        return d

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    consultations = db.relationship('Consultation', backref='user', lazy=True)
    reports = db.relationship('Report', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Consultation(db.Model):
    __tablename__ = 'consultations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(256))
    raw_text = db.Column(db.Text)
    indicators = db.Column(db.Text)  # JSON string
    interpretation = db.Column(db.Text)
    advice = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_indicators(self):
        return json.loads(self.indicators) if self.indicators else []

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'raw_text': self.raw_text,
            'indicators': self.get_indicators(),
            'interpretation': self.interpretation,
            'advice': self.advice,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    symptoms = db.Column(db.Text)  # JSON array of symptom keywords
    advice = db.Column(db.Text)    # 挂号建议

    def get_symptoms(self):
        return json.loads(self.symptoms) if self.symptoms else []

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'symptoms': self.get_symptoms(),
            'advice': self.advice
        }
