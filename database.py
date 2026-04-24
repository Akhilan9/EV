from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    wallet_balance = db.Column(db.Float, default=0.0)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    blockchain_hash = db.Column(db.String(255), nullable=True)
    encrypted_data = db.Column(db.Text, nullable=True)
    receipt_token = db.Column(db.String(36), default=lambda: str(uuid.uuid4()))
    encryption_node = db.Column(db.String(50), default="Edge-Node-1")

class StationNode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default="Online") # Online, Charging, Maintenance, Offline
    health = db.Column(db.Integer, default=100) # Percentage
    energy_output = db.Column(db.Float, default=0.0) # kWh
    coordinates_x = db.Column(db.Integer) # For SVG Map
    coordinates_y = db.Column(db.Integer) # For SVG Map
    last_sync = db.Column(db.DateTime, default=datetime.utcnow)

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
