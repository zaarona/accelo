from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username
        }