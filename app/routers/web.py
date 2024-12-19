from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, send_from_directory
from database import db

bp = Blueprint('web', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login')
def login():
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('web.login'))

@bp.route('/assets/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('assets', path)
    except FileNotFoundError:
        return send_from_directory(path)


