from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file
from flask_login import login_required
from .functions import *
from database import db
from models.version import Version
import pandas as pd
import numpy as np
import json
import time
import os
import zlib
import base64

bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/template.xlsx')
def download_template():
    return send_file('files/template.xlsx')


@bp.route('/upload/<string:project_name>/<string:version_name>', methods=['POST'])
def upload_data(project_name, version_name):
    version = db.session.query(Version).filter_by(version_name=version_name).first()
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        # Create directory structure
        upload_folder = f'../cloud/{project_name}/{version_name}/input'
        output_folder = f'../cloud/{project_name}/{version_name}/output'
        
        for folder in [upload_folder, output_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        # Save file
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        
        # Update version record
        version.input_file_path = file_path
        version.status = 'processing'
        db.session.commit()
        excel_data = pd.ExcelFile(version.input_file_path, engine='openpyxl')
        sheets_data = {}
        for sheet_name in excel_data.sheet_names:
            df = excel_data.parse(sheet_name)
            df.fillna('', inplace=True)  # Replace NaN values with empty strings
            # save the sheet as csv
            df.to_csv(f'../cloud/{project_name}/{version_name}/input/{sheet_name}.csv', index=False)
            # Convert timestamps to string format
            for column in df.select_dtypes(include=['datetime64[ns]']).columns:
                df[column] = df[column].dt.strftime('%Y-%m-%d %H:%M:%S')
            sheets_data[sheet_name.replace('_', '-').lower()] = {
                "name": sheet_name.replace('_',' ').title(),
                "id": sheet_name.replace('_', '-').lower(),
                "type": "table",
                "data": [df.columns.tolist()] + df.values.tolist()
            }

        json_data = json.dumps(sheets_data)
        compressed = zlib.compress(json_data.encode('utf-8'), level=9)  # Ensure maximum compression
        compressed_b64 = base64.b64encode(compressed).decode('utf-8')
        
        # Save to file and return
        with open(f'../cloud/{project_name}/{version_name}/input/data.zip', 'w') as f:
            f.write(compressed_b64)

        # run the cross sell model
        config = {
            'project_name': project_name,
            'version_name': version_name,
            'data_file_path': os.path.join(upload_folder, file.filename),
            'this_year': int(str(time.localtime().tm_year)),
            'breakdown_params': {

            },
            'percentile' : 0.75,
            'quartile_function': 'QUARTILE.EXC',
            'breakdown_column': 'Product Super Family',
            'cohort_columns': 'Common Industry',
            'minimum_sample_size': 41,
            'aggregation_variable': 'AVERAGE',
        }

        # save the config to json file
        config_file_path = f'../cloud/{project_name}/{version_name}/config.json'
        with open(config_file_path, 'w') as config_file:
            json.dump(config, config_file, cls=NpEncoder)

        write_data(config)
        print('Data written running model')
        runXSQuantModel(config)        
        return jsonify({'message': 'File uploaded successfully'})
    
    return jsonify({'error': 'Error while uploading file'}), 500

@bp.route('/data-sheet/<string:project_name>/<string:version_name>', methods=['GET'])
def get_data_sheet(project_name, version_name):
    version = db.session.query(Version).filter_by(
        project_name=project_name,
        version_name=version_name
    ).first()

    if not version or not version.input_file_path:
        excel_data = pd.ExcelFile('files/template.xlsx', engine='openpyxl')
        sheets_data = {}
        for sheet_name in excel_data.sheet_names:
            df = excel_data.parse(sheet_name)
            df.fillna('', inplace=True)
            sheets_data[sheet_name.replace('_','-').lower()] = {
                "name": sheet_name.replace('_',' ').title(),
                "id": sheet_name.replace('_', '-').lower(),
                "type": "table",
                "data": [df.columns.tolist()] + df.values.tolist()
            }
        json_data = json.dumps(sheets_data)
        compressed = zlib.compress(json_data.encode('utf-8'), level=9)  # Ensure maximum compression
        compressed_b64 = base64.b64encode(compressed).decode('utf-8')
        return compressed_b64

    try:
        return send_file(f'../cloud/{project_name}/{version_name}/input/data.zip')
    except FileNotFoundError:
        pass


