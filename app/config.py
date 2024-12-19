import os

class Config:
    # Flask Settings
    HOST = "0.0.0.0"
    PORT = 5253
    DEBUG = True
    ENV = "development"
    
    # Construct Database URL
    SQLALCHEMY_DATABASE_URI = "sqlite:///accelo.db"
    
    # Security
    SECRET_KEY = "acceloSecretKey21!"

def get_config():
    """Get configuration based on environment."""
    env = os.getenv("FLASK_ENV")
    return Config()
