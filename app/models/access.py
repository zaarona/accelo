from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class UserProjectAccess(BaseModel):
    __tablename__ = 'user_project_access'

    username = Column(String(50), ForeignKey('users.username'), nullable=False)
    project_name = Column(String(50), ForeignKey('projects.project_name'), nullable=False)
