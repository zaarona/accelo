from flask import Blueprint, request, jsonify, session, redirect, url_for, send_file, Response
from flask_cors import CORS
from database import db
from models.project import Project
from models.version import Version
from models.user import User
import os
import json
import time
import pandas as pd
import zlib
import base64
import numpy as np


bp = Blueprint('api', __name__, url_prefix='/api')
CORS(bp, resources={r'/*': {'origins': '*'}})

# User endpoints
@bp.route('/users', methods=['GET'])
def get_users():
    users = db.session.query(User).all()
    users = [u.to_dict() for u in users]
    return jsonify(users)

@bp.route('/projects/<string:project_name>/users', methods=['POST'])
def update_project_users(project_name):
    project = db.session.query(Project).filter_by(project_name=project_name).first()
    project.users = request.json.get('users')
    db.session.commit()
    return jsonify({'message': 'Project users updated successfully'})


# Project endpoints
@bp.route('/projects', methods=['GET'])
def get_projects():
    projects = db.session.query(Project).all()
    projects = [p.to_dict() for p in projects]
    for p in projects:
        p['versions'] = [v.to_dict() for v in db.session.query(Version).filter_by(project_name=p['project_name']).all()]
    return jsonify(projects)

@bp.route('/projects', methods=['POST'])
def create_project():
    data = request.json
    if session.get('username') is None:
        session['username'] = 'admin'
    project = Project(
        project_name=data['project_name'],
        description=data.get('description'),
        client_name=data['client_name'],
        created_by=session['username'],
        users=[session['username']]
    )
    db.session.add(project)
    db.session.commit()
    
    # Create initial version
    version = Version(
        project_name=data['project_name'],
        version_name='initial',
        description="Initial version",
        created_by=session['username']
    )
    db.session.add(version)
    db.session.commit()
    
    return jsonify({
        'id': project.id,
        'project_name': project.project_name,
        'message': 'Project created successfully'
    })

@bp.route('/projects/<string:project_name>/versions', methods=['POST'])
def create_version(project_name):
    if session.get('user_id') is None:
        session['username'] = 'admin'
    
    project = db.session.query(Project).filter_by(project_name=project_name).first()

    version = Version(
        project_name=project_name,
        version_name=request.json.get('version_name'),
        description=request.json.get('description'),
        created_by=session['username']
    )
    db.session.add(version)
    db.session.commit()
    
    return jsonify({
        'id': version.id,
        'version_name': version.version_name,
        'message': 'Version created successfully'
    })

