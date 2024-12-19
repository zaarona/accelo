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
bp = Blueprint('fact_pack', __name__, url_prefix='/fact-pack')

@bp.route('/<project_name>/<version_name>', methods=['GET'])
def fact_pack_data(project_name, version_name):
    date = request.args.get('date', datetime.datetime(2021,12,31))
    breakdown_column = request.args.get('breakdown_column', 'Product Super Family')
    cohort_column = request.args.get('cohort_column', 'Common Industry')
    filter_column = request.args.get('filter_column', None)
    filter_value = request.args.get('filter_value', None)
    bundling_filters = request.args.get('bundling_filters', {})
    selected_breakdown = request.args.get('selected_breakdown', None)
    bundling_table_type = request.args.get('bundling_table_type', None)
    data = factpack(project_name, version_name, date, breakdown_column, cohort_column='Common Industry', filter_column=None, filter_value=None, bundling_filters = bundling_filters, selected_breakdown = selected_breakdown, requestor=None, bundling_table_type=bundling_table_type)
    data['data_cube']['id'] = 'data-cube'
    data['data_cube']['name'] = 'Data Cube'
    sheets_data = {
        'data-cube': data['data_cube'],
        'arrs': {
            'id': 'arrs',
            'name': 'ARRs',
            'arrs': data['arrs'],
            'arrs_chartjs': data['arrs_chartjs'],
            'breakdown_list': data['breakdown_list'],
            'filter_values': data['filter_values'],
        },
        'pareto-analysis': {
            'id': 'pareto-analysis',
            'name': 'Pareto Analysis',
            'arr_dist_table': data['arr_dist_table'],
            'pareto_analysis': data['pareto_analysis'],
            'pareto_analysis_chartjs': data['pareto_analysis_chartjs'],
            'breakdown_list': data['breakdown_list'],
            'filter_values': data['filter_values'],
        },
        'attach-rates': {
            'id': 'attach-rates',
            'name': 'Attach Rates',
            'attach_rates_table': data['attach_rates_table'],
            'attach_rates_chartjs': data['attach_rates_chartjs'],
            'breakdown_list': data['breakdown_list'],
            'filter_values': data['filter_values'],
        },
        'bundling': {
            'id': 'bundling',
            'name': 'Bundling',
            'bundling_table': data['bundling_table'],
            'cohort_lists': data['cohort_lists'],
            'breakdown_list': data['breakdown_list'],
            'filter_values': data['filter_values'],
        },
    }   
    json_data = json.dumps(sheets_data)
    compressed = zlib.compress(json_data.encode('utf-8'), level=9)  # Ensure maximum compression
    compressed_b64 = base64.b64encode(compressed).decode('utf-8')
    return compressed_b64


@bp.route('/tab_data_cube/<project_name>/<version_name>', methods=['GET'])
def cross_sell_tab_data_cube(project_name, version_name):
    date = request.args.get('date')
    breakdown_column = request.args.get('breakdown_column')
    return factpack(project_name, version_name, date, breakdown_column, cohort_column='Common Industry', requestor='data_cube')

@bp.route('/tab_arrs/<project_name>/<version_name>', methods=['GET'])
def cross_sell_tab_arrs(project_name, version_name):
    date = request.args.get('date')
    breakdown_column = request.args.get('breakdown_column')
    cohort_column = request.args.get('cohort_column')
    return factpack(project_name, version_name, date, breakdown_column, cohort_column, requestor='arrs')

@bp.route('/tab_pareto_analysis/<project_name>/<version_name>', methods=['GET'])
def cross_sell_tab_pareto_analysis(project_name, version_name):
    date = request.args.get('date')
    cohort_column = request.args.get('cohort_column')
    breakdown_column = 'Product Super Family'
    filter_column = request.args.get('filter_column', None)
    filter_value = request.args.get('filter_value', None)
    if filter_column == 'null':
        filter_column = None
    if filter_value == 'null':
        filter_value = None
    return factpack(project_name, version_name, date, breakdown_column, cohort_column, filter_column, filter_value, requestor='pareto_analysis')

@bp.route('/tab_attach_rates/<project_name>/<version_name>', methods=['GET'])
def cross_sell_tab_attach_rates(project_name, version_name):
    date = request.args.get('date')
    cohort_column = request.args.get('cohort_column', 'Common Geo')
    breakdown_column = request.args.get('breakdown_column', 'Product Super Family')
    filter_column = request.args.get('filter_column', None)
    filter_value = request.args.get('filter_value', None)
    return factpack(project_name, version_name, date, breakdown_column, cohort_column, filter_column, filter_value, requestor='attach_rates')

@bp.route('/tab_bundling/<project_name>/<version_name>', methods=['GET'])
def cross_sell_tab_bundling(project_name, version_name):
    date = request.args.get('date')
    breakdown_column = request.args.get('breakdown_column', 'Product Super Family')
    selected_breakdown = request.args.get('selected_breakdown', None)
    revenue_bucket = request.args.get('revenue_bucket', 'All')
    spend_bucket = request.args.get('spend_bucket', 'All')
    common_industry = request.args.get('common_industry', 'All')
    common_geo = request.args.get('common_geo', 'All')
    segment = request.args.get('segment', 'All')
    bundling_table_type = request.args.get('table_type', None)
    bundling_filters = {
        'Revenue Bucket': revenue_bucket,
        'Spend Bucket': spend_bucket,
        'Common Industry': common_industry,
        'Common Geo': common_geo,
        'Segment': segment
    }
    return factpack(project_name, version_name, date, breakdown_column, cohort_column='Common Industry', filter_column=None, filter_value=None, bundling_filters = bundling_filters, selected_breakdown = selected_breakdown, requestor='bundling', bundling_table_type=bundling_table_type)

def factpack(project_name, version_name, date, breakdown_column, cohort_column='Common Industry', filter_column=None, filter_value=None, bundling_filters={}, selected_breakdown=None, requestor=None, bundling_table_type=None):
    breakdown_list, data_cube, filter_values, arrs, pareto_analysis, attach_rates, bundling_table, cohort_lists = create_factbook(project_name, version_name, date, breakdown_column, cohort_column, filter_column=filter_column, filter_value=filter_value, bundling_filters=bundling_filters, selected_breakdown=selected_breakdown, requestor=requestor, bundling_table_type=bundling_table_type)
    toreturn = {
        'data_cube': {
                'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in data_cube.columns],
                'rowData': data_cube.fillna('').to_dict(orient='records'),
        }
    }
    if arrs is not None:
        arrs['Total'] = arrs[breakdown_list].sum(axis=1)
        breakdown_list = breakdown_list.tolist()
        arrs_heatarr = []
        for col in breakdown_list:
            arrs_heatarr += arrs[col].tolist()
        pinnedBottomRowData = [
                {
                    cohort_column: 'Total ($M)',
                    'Total': '{:,.0f}'.format(round(arrs['Total'].sum() / 1000000)) + 'M',
                    **{col: '{:,.0f}'.format(round(arrs[col].sum() / 1000000)) + 'M' for col in breakdown_list}
                },
                {
                    cohort_column: '% of Total ARR',
                    'Total': '{:,.0f}'.format(round(arrs['Total'].sum() / arrs['Total'].sum() * 100, 1)),
                    **{col: '{:,.0f}'.format(round(arrs[col].sum()  / arrs['Total'].sum() * 100, 2)) + '%'  for col in breakdown_list}
                },
                {
                    cohort_column: 'Total Accounts',
                    'Total': '{:,.0f}'.format(round(len(data_cube) / 1000), 1) + 'K',
                    **{col: '{:,.0f}'.format(round(float((data_cube[col] > 0).sum()) / 1000, 1)) + 'K'  for col in breakdown_list}
                },
                {
                    cohort_column: '% of Total Accounts',
                    'Total': '100%',
                    **{col: '{:,.0f}'.format(round((data_cube[col] > 0).sum() / len(data_cube) * 100, 2)) + '%' for col in breakdown_list}
                },
                {
                    cohort_column: '$ Per Account ($K)',
                    'Total': '${:,.0f}'.format(round(arrs['Total'].sum() / len(data_cube) / 1000)),
                    **{col: '${:,.0f}'.format(round(arrs[col].sum() / len(data_cube) / 1000)) for col in breakdown_list}
                }
            ]
        arrs_chartjs = {
            'labels': eval(str(breakdown_list).replace("' '", "','")),
            'datasets': [{'data': arrs.loc[i][breakdown_list].tolist(), 'label': arrs.loc[i, cohort_column]} for i in range(arrs.shape[0])]
        }

        # for col in breakdown_list + ['Total']:
        #     arrs[col] = arrs[col].apply(lambda x: '{:,.0f}'.format(round(x/1000000, 1))  if x > 0 else '-')
        toreturn['arrs'] = {
            'columnDefs': [
                {'headerName': 'Account Demographics', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 140} for col in [cohort_column] ]},
                {'headerName': 'Total', 'field': 'Total', 'filter':True, 'cellDataType': 'text',  'minWidth': 80},
                {'headerName': 'ARR ($M)', 'children' : [{'field': col, 'filter':True, 'cellDataType': 'text', 'minWidth': 50} for col in breakdown_list]}
            ],
            'rowData': arrs.fillna('').to_dict(orient='records'),
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
            },
            'pinnedBottomRowData': pinnedBottomRowData,
            'arrs_heatarr': arrs_heatarr,
            'cohort_column': cohort_column,
            'cohort_list': arrs[cohort_column].tolist()
        }
        toreturn['arrs_chartjs'] = arrs_chartjs
    if pareto_analysis is not None:
        pinnedBottomRowData = [{
            'Account ID': 'Total ($M)',
            'Total': '',
            'Percentage': '',
            'Cumulative Percentage': '{:,.0f}'.format(round(pareto_analysis['Total'].sum() / 1000000, 1)) + 'M',
        }, {
            'Account ID': 'Total Accounts',
            'Total': '',
            'Percentage': '',
            'Cumulative Percentage': '{:,.0f}'.format(round(len(pareto_analysis) / 1000, 1)) + 'K',
        },  {
            'Account ID': 'Avg. $ per Account ($K)',
            'Total': '',
            'Percentage': '',
            'Cumulative Percentage': '{:,.0f}'.format(round(pareto_analysis['Total'].sum() / len(pareto_analysis) / 1000, 1)) + 'K',
        }]
        pareto_analysis['Cumulative Percentage'] = pareto_analysis['Percentage'].cumsum()
        percentage_list = pareto_analysis['Percentage'].tolist()
        cum_percentage_list = pareto_analysis['Cumulative Percentage'].tolist()
        
        arr_dist_table = [{
            'Measure': 'Top 10 Accounts',
            'ARR ($M)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(10).sum() / 1000000, 1)) + 'M',
            '# of Accounts': len(pareto_analysis['Total'].head(10)),
            '$ per Account ($K)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(10).sum() / len(pareto_analysis['Total'].head(10)) / 1000, 1)) + 'K',
            'peraccountdata': round(pareto_analysis['Total'].head(10).sum() / len(pareto_analysis['Total'].head(10)) / 1000, 1)
        },{
            'Measure': 'Top 10% ',
            'ARR ($M)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.1)).sum() / 1000000, 1)) + 'M',
            '# of Accounts': int(len(pareto_analysis) * 0.1),
            '$ per Account ($K)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.1)).sum() / int(len(pareto_analysis) * 0.1) / 1000, 1)) + 'K',
            'peraccountdata': round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.1)).sum() / int(len(pareto_analysis) * 0.1) / 1000, 1)
        },{
            'Measure': 'Top 20% ',
            'ARR ($M)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.2)).sum() / 1000000, 1)) + 'M',
            '# of Accounts': int(len(pareto_analysis) * 0.2),
            '$ per Account ($K)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.2)).sum() / int(len(pareto_analysis) * 0.2) / 1000, 1)) + 'K',
            'peraccountdata': round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.2)).sum() / int(len(pareto_analysis) * 0.2) / 1000, 1)
        },{
            'Measure': 'Top 50% ',
            'ARR ($M)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.5)).sum() / 1000000, 1)) + 'M',
            '# of Accounts': int(len(pareto_analysis) * 0.5),
            '$ per Account ($K)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.5)).sum() / int(len(pareto_analysis) * 0.5) / 1000, 1)) + 'K',
            'peraccountdata': round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.5)).sum() / int(len(pareto_analysis) * 0.5) / 1000, 1)
        },{
            'Measure': 'Top 75% ',
            'ARR ($M)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.75)).sum() / 1000000, 1)) + 'M',
            '# of Accounts': int(len(pareto_analysis) * 0.75),
            '$ per Account ($K)': '{:,.0f}'.format(round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.75)).sum() / int(len(pareto_analysis) * 0.75) / 1000, 1)) + 'K',
            'peraccountdata': round(pareto_analysis['Total'].head(int(len(pareto_analysis) * 0.75)).sum() / int(len(pareto_analysis) * 0.75) / 1000, 1)
        }]

        pareto_analysis['Total'] = pareto_analysis['Total'].apply(lambda x: '{:,.0f}'.format(round(x/1000, 1)) + 'K'  if x > 0 else '-')
        pareto_analysis['Percentage'] = pareto_analysis['Percentage'].apply(lambda x: '{:,.1f}'.format(x) + '%'  if x > 0 else '-')
        pareto_analysis['Cumulative Percentage'] = pareto_analysis['Cumulative Percentage'].apply(lambda x: '{:,.1f}'.format(x) + '%'  if x > 0 else '-')

        


        toreturn['pareto_analysis'] = {
            'columnDefs': [
                # [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in pareto_analysis.columns],
                { 'headerName': 'Account Demographics', 'children': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in ['Account ID', 'Account Name']]},
                { 'headerName': 'Total', 'field': 'Total', 'filter':True, 'cellDataType': 'text'},
                { 'headerName': 'Percentage', 'field': 'Percentage', 'filter':True, 'cellDataType': 'text'},
                { 'headerName': 'Cumulative Percentage', 'field': 'Cumulative Percentage', 'filter':True, 'cellDataType': 'text'},
            ],
            'rowData': pareto_analysis.fillna('').to_dict(orient='records'),
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
                'defaultMinWidth': 100,
            },
            'pinnedBottomRowData': pinnedBottomRowData
        }
        toreturn['arr_dist_table'] = {
            'columnDefs': [
                {'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in arr_dist_table[0].keys() if col != 'peraccountdata'],
            'rowData': arr_dist_table,
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
                'defaultMinWidth': 100,
            },
        }
        toreturn['pareto_analysis_chartjs'] = {
            'labels': [i for i in range(1, pareto_analysis.shape[0] + 1)],
            'datasets': [
                {
                    'label': 'Top 10 Accounts',
                    'data': cum_percentage_list[:10],
                    'fill': True,
                    'backgroundColor': 'rgba(0, 99, 255, 0.2)',
                },
                {
                    'label': 'Top 10%',
                    'data': [None for a in cum_percentage_list[:10]] + cum_percentage_list[10:int(len(pareto_analysis)*.1)],
                    'fill': True,
                    'backgroundColor': 'rgba(0, 99, 255, 0.2)',
                },
                {
                    'label': 'Top 20%',
                    'data': [None for a in cum_percentage_list[:int(len(pareto_analysis)*.1)]] + cum_percentage_list[int(len(pareto_analysis)*.1):int(len(pareto_analysis)*.2)],
                    'fill': True,
                    'backgroundColor': 'rgba(0, 99, 255, 0.2)',
                },
                {
                    'label': 'Top 50%',
                    'data': [None for a in cum_percentage_list[:int(len(pareto_analysis)*.2)]] + cum_percentage_list[int(len(pareto_analysis)*.2):int(len(pareto_analysis)*.5)],
                    'fill': True,
                    'backgroundColor': 'rgba(0, 99, 255, 0.2)',
                },
                {
                    'label': 'Top 75%',
                    'data': [None for a in cum_percentage_list[:int(len(pareto_analysis)*.5)]] + cum_percentage_list[int(len(pareto_analysis)*.5):int(len(pareto_analysis)*.75)],
                    'fill': True,
                    'backgroundColor': 'rgba(0, 99, 255, 0.2)',
                },
                {
                    'label': 'Bottom 25%',
                    'data': [None for a in cum_percentage_list[:int(len(pareto_analysis)*.75)]] + cum_percentage_list[int(len(pareto_analysis)*.75):],
                    'fill': True,
                    'backgroundColor': 'rgba(0, 99, 255, 0.2)',
                }
            ]
        }
    if attach_rates is not None:
        heatmap_data = []
        for col in breakdown_list:
            heatmap_data += attach_rates[col].tolist()
        for col in breakdown_list:
            attach_rates.loc[attach_rates[breakdown_column] == col, col] = '-'
        
        toreturn['attach_rates_table'] = {
            'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in attach_rates.columns],
            'rowData': attach_rates.fillna('').to_dict(orient='records'),
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
            },
            'heatmap_data': heatmap_data,
        }
        toreturn['attach_rates_chartjs'] = {
            'labels': [col for col in attach_rates.columns if col != breakdown_column],
            'datasets': [{
                'data': attach_rates[col].tolist(),
                'label': col
            } for col in attach_rates.columns if col != breakdown_column]
        }
    if filter_values is not None:
        toreturn['filter_values'] = filter_values
    if bundling_table is not None:
        bundling_table = (bundling_table * 100).round(1)
        heatmap_data = []
        for col in bundling_table.columns:
            heatmap_data += bundling_table[col].tolist()
        bundling_table[breakdown_column] = bundling_table.index
        # set breakdown column as first column
        cols = bundling_table.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        bundling_table = bundling_table[cols]
        toreturn['bundling_table'] = {
            'columnDefs': [{'headerName': col, 'field': col, 'filter':True, 'cellDataType': 'text'} for col in bundling_table.columns],
            'rowData': bundling_table.fillna('').to_dict(orient='records'),
            'autoSizeStrategy': {
                'type': 'fitGridWidth',
            },
            'heatmap_data': heatmap_data
        }
        # toreturn['bundling_chartjs'] = {
        #     'labels': ['#'+col for col in bundling_table.columns],
        #     'datasets': [{
        #         'data': bundling_table.loc[i].tolist(),
        #         'label': str(i)
        #     } for i in bundling_table.index]
        # }
        toreturn['cohort_lists'] = cohort_lists
    if requestor:
        if requestor != 'data_cube':
            toreturn['data_cube'] = []
        if requestor != 'pareto_analysis':
            toreturn['pareto_analysis'] = []
            toreturn['pareto_analysis_chartjs'] = []
        if requestor != 'arrs':
            toreturn['arrs'] = []
            toreturn['arrs_chartjs'] = []
        if requestor != 'attach_rates':
            toreturn['attach_rates'] = []
            toreturn['attach_rates_chartjs'] = []
        if requestor != 'bundling':
            toreturn['bundling_chartjs'] = []
            toreturn['cohort_lists'] = []

    # save to csv
    if requestor == 'data_cube':
        data_cube.to_csv(f'../cloud/{project_name}/{version_name}' + '/output/data_cube.csv', index=False)
    if requestor == 'pareto_analysis':
        pareto_analysis.to_csv(f'../cloud/{project_name}/{version_name}' + '/output/pareto_analysis.csv', index=False)
    if requestor == 'arrs':
        arrs.to_csv(f'../cloud/{project_name}/{version_name}' + '/output/arrs.csv', index=False)
    if requestor == 'attach_rates':
        attach_rates.to_csv(f'../cloud/{project_name}/{version_name}' + '/output/attach_rates_table.csv', index=False)
    if requestor == 'bundling':
        bundling_table.to_csv(f'../cloud/{project_name}/{version_name}' + '/output/bundling_charts.csv', index=False)

    toreturn['breakdown_list'] = [breakdown_list[i] for i in range(len(breakdown_list))]
    return toreturn
