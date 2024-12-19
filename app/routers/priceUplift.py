import os
import json
import time
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file
from .functions import *
import zlib
import base64
import datetime
bp = Blueprint('price_uplift', __name__, url_prefix='/price-uplift')


@bp.route('/<project_name>/<version_name>', methods=['GET'])
def price_uplift_data(project_name, version_name):
    date = request.args.get('date', '2021-12-31')
    percentile_cohort = request.args.get('percentile_cohort', 'Revenue Bucket')
    breakdown_column = request.args.get('breakdown_column', 'Product Super Family')
    cohort_columns = 'Common Industry'
    revenue_spend_toggle = request.args.get('revenue_spend_toggle', 'Spend')
    minimum_sample_size = 10.3
    minimum_seats = 5

    product_super_family_1 = request.args.get('product_super_family_1', 'All')
    product_family_1 = request.args.get('product_family_1', 'All')
    revenue_bucket_1 = request.args.get('revenue_bucket_1', 'All')
    spend_bucket_1 = request.args.get('spend_bucket_1', 'All')
    common_industry_1 = request.args.get('common_industry_1', 'All')
    common_geo_1 = request.args.get('common_geo_1', 'All')
    segment_1 = request.args.get('segment_1', 'All')

    product_super_family_2 = request.args.get('product_super_family_2', 'All')
    product_family_2 = request.args.get('product_family_2', 'All')
    revenue_bucket_2 = request.args.get('revenue_bucket_2', 'All')
    spend_bucket_2 = request.args.get('spend_bucket_2', 'All')
    common_industry_2 = request.args.get('common_industry_2', 'All')
    common_geo_2 = request.args.get('common_geo_2', 'All')
    segment_2 = request.args.get('segment_2', 'All')

    percentile_filters_1 = {
        'Product Super Family': product_super_family_1,
        'Product Family': product_family_1,
        'Revenue Bucket': revenue_bucket_1,
        'Spend Bucket': spend_bucket_1,
        'Common Industry': common_industry_1,
        'Common Geo': common_geo_1,
        'Segment': segment_1
    }
    percentile_filters_2 = {
        'Product Super Family': product_super_family_2,
        'Product Family': product_family_2,
        'Revenue Bucket': revenue_bucket_2,
        'Spend Bucket': spend_bucket_2,
        'Common Industry': common_industry_2,
        'Common Geo': common_geo_2,
        'Segment': segment_2
    }

    sheets_data = {
        'asp-build': {
            'name': 'ASP Build',
            'id': 'asp-build',
            'data': xs_quant_pricing_build(project_name, version_name, date, percentile_cohort, percentile_filters_1, percentile_filters_2, breakdown_column, revenue_spend_toggle, cohort_columns, minimum_sample_size)
        },
        'customer-non-sku': {
            'name': 'Customer Non-SKU',
            'id': 'customer-non-sku',
            'data': xs_quant_uplift(project_name, version_name, date, percentile_cohort, percentile_filters_1, percentile_filters_2, breakdown_column, revenue_spend_toggle, cohort_columns, minimum_sample_size)
        }
    }

    json_data = json.dumps(sheets_data)
    compressed = zlib.compress(json_data.encode('utf-8'), level=9)  # Ensure maximum compression
    compressed_b64 = base64.b64encode(compressed).decode('utf-8')
    return compressed_b64

@bp.route('/tab_asp_build/<project_name>/<version_name>', methods=['GET'])
def xs_quant_pricing_build(project_name, version_name, date, percentile_cohort, percentile_filters_1, percentile_filters_2, breakdown_column, revenue_spend_toggle, cohort_columns, minimum_sample_size):
    minimum_seats = 5

    cohort_lists, pricing_build_1, asp_percentile_table_1, licence_quantity_percentile_table_1, sample_size_table_1, arr_filtered_table_1, arr_unfiltered_table_1 = create_customer_asp(project_name, version_name, date, minimum_seats, percentile_cohort, percentile_filters_1, minimum_sample_size)
    cohort_lists, pricing_build_2, asp_percentile_table_2, licence_quantity_percentile_table_2, sample_size_table_2, arr_filtered_table_2, arr_unfiltered_table_2 = create_customer_asp(project_name, version_name, date, minimum_seats, percentile_cohort, percentile_filters_2, minimum_sample_size)
    return {
        'cohort_lists': cohort_lists,
        'selection1':{
            'asp_percentile_table': asp_percentile_table_1,
            'licence_quantity_percentile_table': licence_quantity_percentile_table_1,
            'sample_size_table': sample_size_table_1,
            'arr_filtered_table': arr_filtered_table_1,
            'arr_unfiltered_table': arr_unfiltered_table_1,
        },
        'selection2':{
            'asp_percentile_table': asp_percentile_table_2,
            'licence_quantity_percentile_table': licence_quantity_percentile_table_2,
            'sample_size_table': sample_size_table_2,
            'arr_filtered_table': arr_filtered_table_2,
            'arr_unfiltered_table': arr_unfiltered_table_2,
        }
    }

@bp.route('/tab_uplift/<project_name>/<version_name>', methods=['GET'])
def xs_quant_uplift(project_name, version_name, date, percentile_cohort, percentile_filters_1, percentile_filters_2, breakdown_column, revenue_spend_toggle, cohort_columns, minimum_sample_size):
    minimum_seats = 5
    max_arr_uplift = 0.5
    yield_uplift_table = {
        '0-25th': 80.0,
        '25-50th': 50.0,
        '50-75th': 10.0,
        '75+': 0
    } 
    yield_uplift_toggle = True
    uplift_table = create_uplift(project_name, version_name, date, breakdown_column, minimum_sample_size, minimum_seats, cohort_columns, revenue_spend_toggle, max_arr_uplift, yield_uplift_toggle, yield_uplift_table)
    return {
        'uplift_table': {
            'columnDefs': [
                {'headerName': 'Account Info', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 120} for col in ['Account ID', 'Account Name'] ]},
                {'headerName': 'Breakdown Column', 'field': breakdown_column, 'filter':True, 'cellDataType': 'text', 'minWidth': 120},
                {'headerName': 'Account Demographics', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 120} for col in ['Revenue Bucket', 'Common Industry','Common Geo','Segment', 'Spend Bucket'] ]},
                {'headerName': 'Revenue Designated Bucket', 'field': 'Revenue Designated Bucket', 'filter':True, 'cellDataType': 'text', 'minWidth': 120},
                {'headerName': 'Revenue Bucket Based', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 90} for col in uplift_table.columns if col.find('Revenue ') > -1 and (col.find('Percentile') > -1  or col.find('Designated') > -1)]},
                {'headerName': 'Spend Bucket Based', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 90} for col in uplift_table.columns if col.find('Spend ') > -1 and (col.find('Percentile') > -1 or col.find('Designated') > -1)]},
                {'headerName': 'Revenue Uplift', 'children': [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 90} for col in ['Current ARR','Implied Uplift','Designated Yield %','Yield Adjusted Uplift','Selected Uplift']]},
            ],
            'rowData': uplift_table.fillna('').to_dict(orient='records'),
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
            },
        }
    }
