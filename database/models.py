from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import db

class User(db.Model):
    """User and administrator authentication model."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Location(db.Model):
    """Geographic locations / monitoring stations for disaster management."""
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    state = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    zone_type = db.Column(db.String(50), default='Urban') # Urban, Suburban, Industrial, Rural
    baseline_temp = db.Column(db.Float, default=32.0)    # Normal summer mean temp (°C)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    weather_records = db.relationship('WeatherData', backref='location', lazy=True, cascade='all, delete-orphan')
    vulnerability = db.relationship('VulnerabilityData', backref='location', uselist=False, cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='location', lazy=True, cascade='all, delete-orphan')
    risk_assessments = db.relationship('RiskAssessment', backref='location', lazy=True, cascade='all, delete-orphan')
    facilities = db.relationship('CriticalFacility', backref='location', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='location', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'state': self.state,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'zone_type': self.zone_type,
            'baseline_temp': self.baseline_temp
        }

class WeatherData(db.Model):
    """Historical and ingested daily meteorological observations."""
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    temperature = db.Column(db.Float, nullable=False)   # Celsius
    humidity = db.Column(db.Float, nullable=False)      # %
    wind_speed = db.Column(db.Float, default=10.0)      # km/h
    rainfall = db.Column(db.Float, default=0.0)         # mm
    pressure = db.Column(db.Float, default=1013.25)     # hPa
    heat_index = db.Column(db.Float, nullable=True)     # Computed NOAA Heat Index
    is_simulated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'rainfall': self.rainfall,
            'pressure': self.pressure,
            'heat_index': self.heat_index,
            'is_simulated': self.is_simulated
        }

class VulnerabilityData(db.Model):
    """Ground-level socio-demographic vulnerability indicators per area."""
    __tablename__ = 'vulnerability_data'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), unique=True, nullable=False)
    total_population = db.Column(db.Integer, nullable=False)
    elderly_count = db.Column(db.Integer, default=0)         # Age 60+
    children_count = db.Column(db.Integer, default=0)        # Age <5
    outdoor_workers_count = db.Column(db.Integer, default=0) # Construction, street vendors, farmers
    slum_residents_count = db.Column(db.Integer, default=0)  # High density informal settlements
    hospital_beds = db.Column(db.Integer, default=50)        # Healthcare capacity
    water_kiosks = db.Column(db.Integer, default=5)          # Public water distribution access
    tree_canopy_ratio = db.Column(db.Float, default=0.15)    # 0.0 - 1.0 (cooling green cover)
    vulnerability_score = db.Column(db.Float, nullable=False)# 0 - 100
    vulnerability_level = db.Column(db.String(20), nullable=False) # LOW, MODERATE, HIGH, EXTREME
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'total_population': self.total_population,
            'elderly_count': self.elderly_count,
            'children_count': self.children_count,
            'outdoor_workers_count': self.outdoor_workers_count,
            'slum_residents_count': self.slum_residents_count,
            'hospital_beds': self.hospital_beds,
            'water_kiosks': self.water_kiosks,
            'tree_canopy_ratio': self.tree_canopy_ratio,
            'vulnerability_score': round(self.vulnerability_score, 1),
            'vulnerability_level': self.vulnerability_level
        }

class Prediction(db.Model):
    """Machine learning inference outputs for heat-wave occurrence."""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    prediction_date = db.Column(db.Date, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    heat_index = db.Column(db.Float, nullable=False)
    predicted_risk = db.Column(db.String(20), nullable=False) # LOW, MODERATE, HIGH, EXTREME
    confidence = db.Column(db.Float, nullable=False)          # 0.0 to 1.0
    model_name = db.Column(db.String(50), default='Random Forest Classifier')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'prediction_date': self.prediction_date.strftime('%Y-%m-%d'),
            'temperature': self.temperature,
            'humidity': self.humidity,
            'heat_index': round(self.heat_index, 1),
            'predicted_risk': self.predicted_risk,
            'confidence': round(self.confidence * 100, 1),
            'model_name': self.model_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class RiskAssessment(db.Model):
    """Composite multidimensional heat risk score (0-100)."""
    __tablename__ = 'risk_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    assessment_date = db.Column(db.Date, nullable=False)
    hazard_score = db.Column(db.Float, nullable=False)
    vulnerability_score = db.Column(db.Float, nullable=False)
    exposure_score = db.Column(db.Float, nullable=False)
    total_risk_score = db.Column(db.Float, nullable=False)    # 0 to 100
    risk_level = db.Column(db.String(20), nullable=False)     # LOW, MODERATE, HIGH, EXTREME
    score_breakdown_json = db.Column(db.Text, nullable=True)  # JSON details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'assessment_date': self.assessment_date.strftime('%Y-%m-%d'),
            'hazard_score': round(self.hazard_score, 1),
            'vulnerability_score': round(self.vulnerability_score, 1),
            'exposure_score': round(self.exposure_score, 1),
            'total_risk_score': round(self.total_risk_score, 1),
            'risk_level': self.risk_level,
            'breakdown': self.score_breakdown_json
        }

class CriticalFacility(db.Model):
    """Facilities used in GIS mapping (Hospitals, Cooling Centers, Water distribution points)."""
    __tablename__ = 'critical_facilities'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    facility_type = db.Column(db.String(50), nullable=False) # Hospital, Cooling Center, Water Point
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, default=100)
    contact_phone = db.Column(db.String(30))

    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'name': self.name,
            'facility_type': self.facility_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'capacity': self.capacity,
            'contact_phone': self.contact_phone
        }

class Alert(db.Model):
    """Early warnings triggered when risk is HIGH or EXTREME."""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False, index=True)
    alert_level = db.Column(db.String(20), nullable=False) # HIGH, EXTREME
    temperature = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    recommended_action = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Active', index=True) # Active, Resolved
    simulated_dispatched = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'alert_level': self.alert_level,
            'temperature': self.temperature,
            'reason': self.reason,
            'recommended_action': self.recommended_action,
            'status': self.status,
            'simulated_dispatched': self.simulated_dispatched,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None
        }

class ResponseRecommendation(db.Model):
    """Rule catalog of standard operating procedures for disaster management."""
    __tablename__ = 'response_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    risk_level = db.Column(db.String(20), nullable=False, index=True) # LOW, MODERATE, HIGH, EXTREME
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    target_sector = db.Column(db.String(50), nullable=False) # Health, Labor, Public, Municipal
    priority = db.Column(db.String(20), nullable=False)      # P1 (Immediate), P2 (Urgent), P3 (Routine)

    def to_dict(self):
        return {
            'id': self.id,
            'risk_level': self.risk_level,
            'title': self.title,
            'description': self.description,
            'target_sector': self.target_sector,
            'priority': self.priority
        }
