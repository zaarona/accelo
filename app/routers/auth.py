from flask import Blueprint, request, jsonify, session, redirect, url_for
from models.user import User
from database import db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = db.session.query(User).filter_by(username=username).first()
    if not user or not user.password == password:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    else:
        session['username'] = username
        return jsonify({"status": "success"}), 200

@bp.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('web.login'))
