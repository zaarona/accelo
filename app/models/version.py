from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import BaseModel

class Version(BaseModel):
    __tablename__ = 'versions'

    project_name = Column(String(50), ForeignKey('projects.project_name'), nullable=False)
    version_name = Column(String(50), nullable=False)
    description = Column(String(120))
    created_by = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    input_file_path = Column(String(255))
    output_file_path = Column(String(255))
    status = Column(String(20), default='created')  # created, processing, completed, error
    
    def to_dict(self):
        return {
            'id': self.id,
            'version_name': self.version_name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }
