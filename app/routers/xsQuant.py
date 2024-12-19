import os
import json
import time
import pandas as pd
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file
from .functions import *
import zlib
import base64

bp = Blueprint('xs_quant', __name__, url_prefix='/xs-quant')

@bp.route('/<project_name>/<version_name>', methods=['GET'])
def xs_quant_data(project_name, version_name):
    common_industry = request.args.get('common_industry', 'All')
    common_geo = request.args.get('common_geo', 'All')
    segment = request.args.get('segment', 'All')
    accounts = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/unique_account_list.csv')
    dealsize = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/deal_size_database.csv')
    cohorts = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/revenue_cohorts.csv')
    opportunities = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/opportunity_database.csv')

    accounts.fillna('', inplace=True)
    dealsize.fillna('', inplace=True)
    cohorts.fillna('', inplace=True)
    opportunities.fillna('', inplace=True)
    sheets_data = {
        'accounts': {
            'name': 'Accounts',
            'type': 'table',
            'id': 'accounts-table',
            'data': [accounts.columns.tolist()] + accounts.values.tolist()
        },
        'deal-size': {
            'name': 'Deal Size',
            'type': 'table',
            'id': 'deal-size-table',
            'data': [dealsize.columns.tolist()] + dealsize.values.tolist()
        },
        'cohorts': {
            'name': 'Cohorts',
            'type': 'table',
            'id': 'cohorts-table',
            'data': [cohorts.columns.tolist()] + cohorts.values.tolist()
        },
        'opportunities': {
            'name': 'Opportunities',
            'type': 'table',
            'id': 'opportunities-table',
            'data': [opportunities.columns.tolist()] + opportunities.values.tolist()
        },
        'cross-sell': {
            'name': 'Cross-Sell',
            'type': 'dashboard',
            'id': 'cross-sell',
            'data': xs_quant_opportunities(project_name, version_name, common_industry, common_geo, segment, 'cross-sell')
        },
        'up-sell': {
            'name': 'Up-Sell',
            'type': 'dashboard',
            'id': 'up-sell',
            'data': xs_quant_opportunities(project_name, version_name, common_industry, common_geo, segment, 'up-sell')
        }
    }
    json_data = json.dumps(sheets_data)
    compressed = zlib.compress(json_data.encode('utf-8'), level=9)  # Ensure maximum compression
    compressed_b64 = base64.b64encode(compressed).decode('utf-8')
    return compressed_b64

@bp.route('/validation/<project_name>/<version_name>', methods=['GET'])
def xs_quant_validation(project_name, version_name):
    # get sales data
    sales_data, product_lookup, industry_lookup, geo_lookup, customer_lookup = get_data({'project_name': project_name, 'version_name': version_name})
    # return aggrid data
            
    return jsonify({
        'sales_data': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in sales_data.columns],
                'rowData': sales_data[:100].fillna('').to_dict(orient='records'),
        },
        'product_lookup': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in product_lookup.columns],
                'rowData': product_lookup[:100].fillna('').to_dict(orient='records'),
        },
        'industry_lookup': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in industry_lookup.columns],
                'rowData': industry_lookup[:100].fillna('').to_dict(orient='records'),
        },
        'geo_lookup': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in geo_lookup.columns],
                'rowData': geo_lookup[:100].fillna('').to_dict(orient='records'),
        },
        'customer_lookup': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in customer_lookup.columns],
                'rowData': customer_lookup[:100].fillna('').to_dict(orient='records'),
        }
    })

@bp.route('/accounts/<project_name>/<version_name>', methods=['GET'])
def xs_quant_accounts(project_name, version_name):
    unique_account_list = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/unique_account_list.csv')
    return jsonify({
        'unique_account_list': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in unique_account_list.columns],
                'rowData': unique_account_list[:100].fillna('').to_dict(orient='records'),
        }
    })

@bp.route('/dealsize/<project_name>/<version_name>', methods=['GET'])
def xs_quant_dealsize(project_name, version_name):
    deal_size_database = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/deal_size_database.csv')
    return jsonify({
        'deal_size_database': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in deal_size_database.columns],
                'rowData': deal_size_database[:100].fillna('').to_dict(orient='records'),
        }
    })

@bp.route('/buckets/<project_name>/<version_name>', methods=['GET'])
def xs_quant_buckets(project_name, version_name):
    # calculate revenue and spend buckets
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    sales_data, product_lookup, industry_lookup, geo_lookup, customer_lookup = get_data(config)
    breakdown_list = sales_data[config['breakdown_column']].unique()
    for breakdown in breakdown_list:
        config['breakdown_params'][breakdown] = 'SUBSCRIPTION'
    unique_account_list, revenue_buckets_labels, spend_buckets_labels, revenue_buckets, spend_buckets = create_unique_account_list(sales_data, config, breakdown_list)
    return jsonify({
        'revenue_buckets': revenue_buckets[2:-1],
        'revenue_buckets_labels': revenue_buckets_labels,
        'revenue_buckets_counts': [len(unique_account_list[unique_account_list['Revenue Bucket'] == bucket]) for bucket in revenue_buckets_labels],
        'spend_buckets': spend_buckets[2:-1],
        'spend_buckets_labels': spend_buckets_labels,
        'spend_buckets_counts': [len(unique_account_list[unique_account_list['Spend Bucket'] == bucket]) for bucket in spend_buckets_labels],
    })

@bp.route('/update-buckets/<project_name>/<version_name>', methods=['POST'])
def xs_quant_update_buckets(project_name, version_name):
    # calculate revenue and spend buckets
    revenue_buckets = request.get_json()['revenue_buckets']
    spend_buckets = request.get_json()['spend_buckets']
    revenue_buckets = [int(bucket) for bucket in revenue_buckets]
    spend_buckets = [int(bucket) for bucket in spend_buckets]
    revenue_buckets = [-np.inf, 0] + revenue_buckets + [np.inf]
    spend_buckets = [-np.inf, 0] + spend_buckets + [np.inf]
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    config['revenue_buckets'] = revenue_buckets
    config['spend_buckets'] = spend_buckets
    # cohort columns, cannot be empty
    if config['cohort_columns'] == '':
        config['cohort_columns'] = 'Common Industry'
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'w') as config_file:
        json.dump(config, config_file, cls=NpEncoder)
    return 'success'

@bp.route('/cohorts/<project_name>/<version_name>', methods=['GET'])
def xs_quant_cohorts(project_name, version_name):
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    runXSQuantModel(config)
    revenue_cohorts = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/revenue_cohorts.csv')
    spend_cohorts = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/spend_cohorts.csv')
    revenue_cohorts = revenue_cohorts.round(2)
    spend_cohorts = spend_cohorts.round(2)
    return jsonify({
        'revenue_cohorts': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in revenue_cohorts.columns],
                'rowData': revenue_cohorts.fillna('').to_dict(orient='records'),
        },
        'spend_cohorts': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in spend_cohorts.columns],
                'rowData': spend_cohorts.fillna('').to_dict(orient='records'),
        }
    })

def xs_quant_opportunities(project_name, version_name, common_industry, common_geo, segment, model_type):
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    config['revenue_buckets'] = config['revenue_buckets'][2:-1]
    config['spend_buckets'] = config['spend_buckets'][2:-1]
    sales_data, product_lookup, industry_lookup, geo_lookup, customer_lookup = get_data(config)
    common_geo_list = sales_data['Common Geo'].unique().tolist()
    common_industry_list = sales_data['Common Industry'].unique().tolist()
    segment_list = sales_data['Segment'].unique().tolist()
    cohort_column_list = sales_data[config['cohort_columns']].unique().tolist()
    if model_type == 'cross-sell':
        opportunities = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/opportunity_database.csv')
    elif model_type == 'up-sell':
        opportunities = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/up_sell_database.csv')

    if 'Common Industry' in opportunities.columns:
        opportunities.drop('Common Industry', axis=1, inplace=True)
    if 'Common Geo' in opportunities.columns:
        opportunities.drop('Common Geo', axis=1, inplace=True)
    if 'Segment' in opportunities.columns:
        opportunities.drop('Segment', axis=1, inplace=True)

    
    opportunities = opportunities.merge(sales_data[['Account ID', 'Common Industry', 'Common Geo', 'Segment']].drop_duplicates(), on='Account ID', how='left')
    if common_industry != 'All' and common_industry != 'null':
        opportunities = opportunities[opportunities['Common Industry'] == common_industry]
    if common_geo != 'All' and common_geo != 'null':
        opportunities = opportunities[opportunities['Common Geo'] == common_geo]
    if segment != 'All' and segment != 'null':
        opportunities = opportunities[opportunities['Segment'] == segment]

    opportunities = opportunities[[col for col in opportunities.columns if col in ['Account Name', 'Account ID'] or col.find('OPPORTUNITY') > -1]]
    opportunities.columns = [col.replace('OPPORTUNITY_VALUE_', '') for col in opportunities.columns]
    opportunities = opportunities.round(0)
    breakdown_list = sales_data[config['breakdown_column']].unique().tolist()
    opportunities['Total'] = opportunities[breakdown_list].sum(axis=1)
    print(opportunities)

    total_opportunities = opportunities[opportunities.columns[2:]].sum().tolist()
    total_accounts = opportunities[opportunities.columns[2:]].apply(lambda x: len(x[x > 0])).tolist()
    average_opportunity_value = [round(opp / acc) if acc > 0 else 0 for opp, acc in zip(total_opportunities, total_accounts)]
    opportunities.sort_values('Total', ascending=False, inplace=True)
    pinnedBottomRowData = [
        {
            'Account Name': 'Total ($M)',
            'Total': '{:,.0f}'.format(round(opportunities['Total'].sum() / 1000000)) + 'M',
            **{col: str(round(opportunities[col].sum() / 1000000)) + 'M' for col in breakdown_list}
        },
        {
            'Account Name': 'Total Accounts',
            'Total': '{:,.0f}'.format(len(opportunities)),
            **{col: '{:,.0f}'.format(len(opportunities[col][opportunities[col] > 0])) for col in breakdown_list}
        },
        {
            'Account Name': 'Avg $ per Account ($K)',
            'Total': '{:,.0f}'.format(round(opportunities['Total'].sum() / len(opportunities) / 1000)) + 'K',
            **{col: '{:,.0f}'.format(round(opportunities[col].sum() / len(opportunities) / 1000)) + 'K' for col in breakdown_list}
        }
    ]

    opportunity_table = opportunities.copy()
    opportunity_table = opportunity_table.merge(sales_data[['Account ID', config['cohort_columns']]] , on='Account ID', how='left')
    opportunity_table.drop('Account ID', axis=1, inplace=True)
    if 'Account Name' in opportunity_table.columns:
        opportunity_table.drop('Account Name', axis=1, inplace=True)
    opportunity_table = opportunity_table.groupby(config['cohort_columns']).sum().reset_index()
    opportunity_table.index = opportunity_table[config['cohort_columns']]
    opportunity_table_arr = []
    for col in breakdown_list:
        opportunity_table_arr += opportunity_table[col].tolist()
    opportunity_table.loc['Total'] = opportunity_table.sum()
    opportunity_table.loc['Total', config['cohort_columns']] = 'Total'
    # opportunity_table['Total'] = opportunity_table[breakdown_list].sum(axis=1)
    # # create total row:
    # opportunity_table.loc['Total'] = opportunity_table.sum()

    opportunities.to_csv(f'../cloud/{project_name}/{version_name}' + '/output/opportunities.csv', index=False)
    opportunity_table.to_csv(f'../cloud/{project_name}/{version_name}' + '/output/opportunity_heatmap.csv', index=False)


    for col in breakdown_list + ['Total']:
        # format numbers to K with decimal separator
        opportunities[col] = opportunities[col].apply(lambda x: '{:,.0f}'.format(round(x/1000)) if x > 0 else '-')
    
    # add total row
    

    return {
        'common_geo_list': ['All'] + common_geo_list,
        'common_industry_list': ['All'] + common_industry_list,
        'segment_list': ['All'] + segment_list,
        'grid': {
            'columnDefs': [
                {'headerName': 'Account Demographics', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 120} for col in ['Account ID', 'Account Name'] ]},
                {'headerName': 'Total', 'field': 'Total', 'filter':True, 'cellDataType': 'text', 'minWidth': 80},
                {'headerName': 'Account Oppurtunity ($ in Thousands)', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 90} for col in breakdown_list]}
            ],
            'rowData': opportunities.fillna('').to_dict(orient='records'),
            'pinnedBottomRowData': pinnedBottomRowData,
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
            },
        },
        'metrics': opportunities[[col for col in opportunities.columns if col not in ['Account Name', 'Account ID']]].sum().to_dict(),
        'opportunity_chartjs_1': {
            'labels':  [x[:14] for x in opportunities.columns[2:].tolist()],
            'datasets': [{
                'data': total_opportunities,
                'label': 'Opportunity Value'    
            }]
        },
        'opportunity_chartjs_2': {
            'labels': [x[:14] for x in opportunities.columns[2:].tolist()],
            'datasets': [{
                    'data': total_accounts,
                    'label': '# of Accounts',
                    'yAxisID': 'y',
                }
            ]
        },
        'opportunity_chartjs_3': {
            'labels': [x[:14] for x in opportunities.columns[2:].tolist()],
            'datasets': [{
                    'data': average_opportunity_value,
                    'label': 'Average Opportunity Value',
                    'yAxisID': 'y',
                }
            ]
        },
        'opportunity_heatmap': {
            'columnDefs': [{'headerName': col, 'field': col, 'cellDataType': 'text'} for col in opportunity_table.columns],
            'rowData': opportunity_table.fillna('').to_dict(orient='records'),
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
                'defaultMinWidth': 100,
            },
        },
        'opportunity_table_arr': opportunity_table_arr,
        'config': config
    }



@bp.route('/update-config/<project_name>/<version_name>', methods=['POST'])
def xs_quant_update_config(project_name, version_name):
    config_file_path = f'../cloud/{project_name}/{version_name}/config.json'
    with open(config_file_path, 'r') as file:
        config = json.load(file)
    data = request.get_json()
    for key in data.keys():
        if key == 'cohort_columns':
            config[key] = ' - '.join(sorted(data[key]))
        elif key in ['this_year', 'minimum_sample_size']:
            config[key] = int(data[key])
        elif key in ['percentile']:
            config[key] = float(data[key])
        elif key == 'breakdown_params':
            for k in data[key].keys():
                config[key][k] = data[key][k]
        elif key == 'revenue_buckets':
            # add minus infinity and infinity to the list
            config[key] = [-np.inf, 0] + data[key] + [np.inf]
        elif key == 'spend_buckets':
            config[key] = [-np.inf, 0] + data[key] + [np.inf]
        else:
            config[key] = data[key]

    # Save file
    with open(config_file_path, 'w') as file:
        json.dump(config, file, cls=NpEncoder)
        
    runXSQuantModel(config)
    return 'success'    

@bp.route('/breakdown-combinations/<project_name>/<version_name>', methods=['GET'])
def xs_quant_breakdown_combinations(project_name, version_name):
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    
    labels = ['Product Super Family', 'Product Family']
    data = {}
    for breakdown_column in labels:
        config['breakdown_column'] = breakdown_column
        opp = runXSQuantModel(config, write_data=False, override_config=False)
        # rename columns remove empty spaces
        opp.columns = [col.replace(' ', '_') for col in opp.columns]
        label = breakdown_column
        opp = opp[[col for col in opp.columns if col.find('OPPORTUNITY_VALUE') > -1]].sum().to_dict()
        data[breakdown_column] = opp

    allkeys = []
    for label in labels:
        for key in data[label].keys():
            allkeys.append(key)
    allkeys = list(set(allkeys))

    datasets = []
    for key in allkeys:
        dataset = {}
        dataset['label'] = key.replace('OPPORTUNITY_VALUE_', '')
        d = []
        for label in labels:
            if key in data[label]:
                d.append(data[label][key])
            else:
                d.append(0)
        dataset['data'] = d
        datasets.append(dataset)
        print(dataset)
        
    return jsonify({
        'labels': labels,
        'datasets': datasets
    })

@bp.route('/cohort-combinations/<project_name>/<version_name>', methods=['GET'])
def xs_quant_cohort_combinations(project_name, version_name):
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    
    labels = ['Common Geo', 'Common Industry', 'Segment', 'Common Geo - Common Industry', 'Common Geo - Segment', 'Common Industry - Segment', 'Common Geo - Common Industry - Segment']
    data = {}
    for cohort_column in labels:
        config['cohort_columns'] = cohort_column
        opp = runXSQuantModel(config, write_data=False, override_config=False)
        # rename columns remove empty spaces
        opp.columns = [col.replace(' ', '_') for col in opp.columns]
        label = cohort_column
        opp = opp[[col for col in opp.columns if col.find('OPPORTUNITY_VALUE') > -1]].sum().to_dict()
        data[cohort_column] = opp

    allkeys = []
    for label in labels:
        for key in data[label].keys():
            allkeys.append(key)
    allkeys = list(set(allkeys))

    datasets = []
    for key in allkeys:
        dataset = {}
        dataset['label'] = key.replace('OPPORTUNITY_VALUE_', '')
        d = []
        for label in labels:
            if key in data[label]:
                d.append(data[label][key])
            else:
                d.append(0)
        dataset['data'] = d
        datasets.append(dataset)
        print(dataset)
        
    return jsonify({
        'labels': labels,
        'datasets': datasets
    })

@bp.route('/percentile-combinations/<project_name>/<version_name>', methods=['GET'])
def xs_quant_percentile_combinations(project_name, version_name):
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    
    labels = [0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
    data = {}
    for percentile in labels:
        config['percentile'] = percentile
        opp = runXSQuantModel(config, write_data=False, override_config=False)
        # rename columns remove empty spaces
        opp.columns = [col.replace(' ', '_') for col in opp.columns]
        label = percentile
        opp = opp[[col for col in opp.columns if col.find('OPPORTUNITY_VALUE') > -1]].sum().to_dict()
        data[percentile] = opp

    allkeys = []
    for label in labels:
        for key in data[label].keys():
            allkeys.append(key)
    allkeys = list(set(allkeys))

    datasets = []
    for key in allkeys:
        dataset = {}
        dataset['label'] = key.replace('OPPORTUNITY_VALUE_', '')
        d = []
        for label in labels:
            if key in data[label]:
                d.append(data[label][key])
            else:
                d.append(0)
        dataset['data'] = d
        datasets.append(dataset)
        print(dataset)
        
    return jsonify({
        'labels': labels,
        'datasets': datasets
    })

@bp.route('/aggregation-combinations/<project_name>/<version_name>', methods=['GET'])
def xs_quant_aggregation_combinations(project_name, version_name):
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    
    labels = ['SPEND', 'REVENUE', 'AVERAGE']
    data = {}
    for aggregation in labels:
        config['aggregation_variable'] = aggregation
        opp = runXSQuantModel(config, write_data=False, override_config=False)
        # rename columns remove empty spaces
        opp.columns = [col.replace(' ', '_') for col in opp.columns]
        label = aggregation
        opp = opp[[col for col in opp.columns if col.find('OPPORTUNITY_VALUE') > -1]].sum().to_dict()
        data[aggregation] = opp

    allkeys = []
    for label in labels:
        for key in data[label].keys():
            allkeys.append(key)
    allkeys = list(set(allkeys))

    datasets = []
    for key in allkeys:
        dataset = {}
        dataset['label'] = key.replace('OPPORTUNITY_VALUE_', '')
        d = []
        for label in labels:
            if key in data[label]:
                d.append(data[label][key])
            else:
                d.append(0)
        dataset['data'] = d
        datasets.append(dataset)
        print(dataset)
        
    return jsonify({
        'labels': labels,
        'datasets': datasets
    })

@bp.route('/download/<project_name>/<version_name>/<string:fn>', methods=['GET'])
def xs_quant_download(project_name, version_name, fn):
    return send_file(f'../cloud/{project_name}/{version_name}/output/{fn}.csv', as_attachment=True)

