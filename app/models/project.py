from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import BaseModel

class Project(BaseModel):
    __tablename__ = 'projects'

    project_name = Column(String(50), nullable=False)
    description = Column(String(120))
    created_by = Column(String(50), nullable=False)
    client_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    users = Column(JSON) # list of usernames
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_name': self.project_name,
            'description': self.description,
            'client_name': self.client_name,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'users': self.users
        }