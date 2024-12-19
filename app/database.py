from flask_sqlalchemy import SQLAlchemy
from config import get_config
from models.base import Base
from models.user import User
from models.project import Project
from models.version import Version

settings = get_config()
db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    db.init_app(app)
    
    with app.app_context():
        Base.metadata.create_all(db.engine)
        
        # Create admin user if it doesn't exist
        admin = db.session.query(User).filter_by(username="admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                password="Fti2024!",
            )
            db.session.add(admin_user)
            db.session.commit()

            # add new user:
            new_user = User(
                username="matt",
                password="Fti2024!",
            )
            db.session.add(new_user)
            db.session.commit()

            # add new user:
            new_user = User(
                username="zach",
                password="Fti2024!",
            )
            db.session.add(new_user)
            db.session.commit()

            # add new user:
            new_user = User(
                username="harun",
                password="Fti2024!",
            )
            db.session.add(new_user)
            db.session.commit() 
            print("new user added")
            # add new project:
            new_project = Project(
                project_name="test",
                users=["admin", "matt", "zach"],
                created_by="admin",
                client_name="test",
                description="test",
            )
            db.session.add(new_project)
            db.session.commit()
            print("new project added")
            # add new version:
            new_version = Version(
                project_name="test",
                version_name="1.0.0",
                description="Initial version",
                created_by="admin",
            )
            db.session.add(new_version)
            db.session.commit()
            print("new version added")