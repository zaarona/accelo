from flask import Flask, request, session, redirect
from flask_cors import CORS
from config import get_config
from routers import api, web, auth, data, xsQuant, factPack, priceUplift, segmentation
from database import db, init_db
import time

settings = get_config()

def create_app():
    app = Flask(__name__, 
        template_folder="templates"
    )

    # Configure app
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG

    # Enable CORS with specific configuration
    CORS(app)

    # Register blueprints
    with app.app_context():
        app.register_blueprint(api.bp)
        app.register_blueprint(web.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(data.bp)
        app.register_blueprint(xsQuant.bp)
        app.register_blueprint(factPack.bp)
        app.register_blueprint(priceUplift.bp)
        app.register_blueprint(segmentation.bp)
        
    # @app.before_request
    # def check_login():
    #     if request.path != '/login' and request.path != '/auth/login' and not session.get('username'):
    #         return redirect('/login')
   
    return app

def wait_for_db(max_retries=5, delay=2):
    retries = 0
    while retries < max_retries:
        try:
            app = create_app()
            with app.app_context():
                init_db(app)
            return app
        except Exception as e:
            print(f"Database connection attempt {retries + 1} failed: {str(e)}")
            retries += 1
            if retries < max_retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    
    raise Exception("Could not connect to database after multiple attempts")

if __name__ == '__main__':
    app = wait_for_db()
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )


