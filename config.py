import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration settings."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartheat-disaster-resilience-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'database', 'smartheat.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Machine Learning and Models
    MODEL_DIR = os.path.join(BASE_DIR, 'saved_models')
    SAMPLE_DATA_DIR = os.path.join(BASE_DIR, 'data')
    DEFAULT_DATASET = os.path.join(BASE_DIR, 'data', 'real_weather_history.csv')
    
    # Configurable Risk Scoring Weights (Must sum to 1.0)
    RISK_WEIGHT_HAZARD = 0.45          # Weather & heat index hazard
    RISK_WEIGHT_VULNERABILITY = 0.30   # Demographics (elderly, children, slums, outdoor labor)
    RISK_WEIGHT_EXPOSURE = 0.15        # Population density and urbanization level
    RISK_WEIGHT_HEALTHCARE_DEFICIT = 0.10 # Healthcare and water accessibility gaps
    
    # Configurable Risk Score Thresholds (0-100)
    THRESHOLD_LOW_MAX = 25.0
    THRESHOLD_MODERATE_MAX = 50.0
    THRESHOLD_HIGH_MAX = 75.0
    # Above 75 is classified as EXTREME
    
    # Meteorological Heat Index Thresholds (Celsius)
    HI_MODERATE_MIN = 32.0   # Extreme caution
    HI_HIGH_MIN = 41.0       # Danger (Heat cramps & exhaustion likely)
    HI_EXTREME_MIN = 54.0    # Extreme danger (Heat stroke imminent)
    ABSOLUTE_HEATWAVE_TEMP = 45.0  # Celsius
