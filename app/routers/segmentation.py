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
from openai import OpenAI
from sklearn.cluster import KMeans

def create_segmentation(data):
    data.rename(columns={'Common Geo': 'Region', 'Common Industry': 'Industry'}, inplace=True)
    data['ACCOUNT_TOTAL_REVENUE'] = data['ACCOUNT_TOTAL_REVENUE'].replace('NO DATA', 0).astype(float)
    data['Current Year Spend'] = data['Current Year Spend'].replace('NO DATA', 0).astype(float)
    features = data[['ACCOUNT_TOTAL_REVENUE', 'Current Year Spend', 'Region', 'Industry']]
    features['ACCOUNT_TOTAL_REVENUE'] = (features['ACCOUNT_TOTAL_REVENUE'] - features['ACCOUNT_TOTAL_REVENUE'].mean()) / features['ACCOUNT_TOTAL_REVENUE'].std()
    features['Current Year Spend'] = (features['Current Year Spend'] - features['Current Year Spend'].mean()) / features['Current Year Spend'].std()
    region_dict = {region: i for i, region in enumerate(features['Region'].unique())}
    features['Region'] = features['Region'].map(region_dict)
    industry_dict = {industry: i for i, industry in enumerate(features['Industry'].unique())}
    features['Industry'] = features['Industry'].map(industry_dict)
    kmeans = KMeans(n_clusters=7)
    data['Segment'] = kmeans.fit_predict(features[['ACCOUNT_TOTAL_REVENUE', 'Current Year Spend']])
    segment_names = [f'Segment {i}' for i in range(len(data['Segment'].unique()))]
    data = data[~((data['ACCOUNT_TOTAL_REVENUE'] > data['ACCOUNT_TOTAL_REVENUE'].mean() + 3 * data['ACCOUNT_TOTAL_REVENUE'].std()) | (data['ACCOUNT_TOTAL_REVENUE'] < data['ACCOUNT_TOTAL_REVENUE'].mean() - 3 * data['ACCOUNT_TOTAL_REVENUE'].std()))]
    data = data[~((data['Current Year Spend'] > data['Current Year Spend'].mean() + 3 * data['Current Year Spend'].std()) | (data['Current Year Spend'] < data['Current Year Spend'].mean() - 3 * data['Current Year Spend'].std()))]
    segment_stats = []
    for i in range(len(segment_names)):
        segment_data = data[data['Segment'] == i]
        segment_stats.append({
            'segment_name': segment_names[i],
            'mean_revenue': segment_data['ACCOUNT_TOTAL_REVENUE'].mean(),
            'mean_spend': segment_data['Current Year Spend'].mean(),
            'count': len(segment_data),
            'min_revenue': segment_data['ACCOUNT_TOTAL_REVENUE'].min(),
            'max_revenue': segment_data['ACCOUNT_TOTAL_REVENUE'].max(),
            'min_spend': segment_data['Current Year Spend'].min(),
            'max_spend': segment_data['Current Year Spend'].max()
        })

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    content = "Give me names for the following segments, only return the names, do not include any other text or comments, give me an array of names: " + str(segment_stats)
    content = content[:10000]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": content}],
        temperature=0.5,
        max_tokens=1000
    )
    segment_names = eval(response.choices[0].message.content)
    
    series = []
    for i in range(len(segment_names)):
        segment_data = data[data['Segment'] == i]
        if len(segment_data) == 0:
            continue
        series.append({
                'name': segment_names[i],
                'type': 'scatter',
                'emphasis': {
                    'focus': 'series'
                },
                'data': data[data['Segment'] == i][['ACCOUNT_TOTAL_REVENUE', 'Current Year Spend', 'Account Name']].values.tolist(),
                'markArea': {
                    'silent': True,
                    'itemStyle': {
                        'color': 'transparent',
                        'borderWidth': 1,
                        'borderType': 'dashed'
                    },
                    'data': [
                        [
                        {
                            'name': segment_names[i] + ' Count: ' + str(len(segment_data)),
                            'xAxis': 'min',
                            'yAxis': 'min'
                        },
                        {
                            'xAxis': 'max',
                            'yAxis': 'max'
                        }
                        ]
                    ],
                    'label': {
                        'show': True
                    }
                },
                'markLine': {
                    'lineStyle': {
                        'type': 'solid'
                    },
                    'data': [ 
                             { 'xAxis': data[data['Segment'] == i]['ACCOUNT_TOTAL_REVENUE'].mean()},
                             { 'yAxis': data[data['Segment'] == i]['Current Year Spend'].mean()}
                             ],
                    'label': {
                        'show': True
                    }
                }
        })
    
    options = {
        'title': {
            'text': 'Segmentation based on Revenue and Spend ',
            'left': 'center',
            'top': '10px',
            'textStyle': {
                'fontSize': 14,
                'fontWeight': 'bold',
                'fontFamily': 'Barlow, sans-serif',
                'color': '#1b645b'
            }
        },
        'legend': {
            'data': [f'Segment {i}' for i in range(len(segment_names))],
            'left': 'center',
            'bottom': 10
        },
        'series': series
    }
    
    return options

bp = Blueprint('segmentation', __name__, url_prefix='/segmentation')



@bp.route('/<project_name>/<version_name>', methods=['GET'])
def segmentation_data(project_name, version_name):
    unique_accounts = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/unique_account_list.csv')
    
    sheets_data = {
        'clustering': {
            'id': 'clustering',
            'name': 'Clustering',
            'data': {
                'options': create_segmentation(unique_accounts)
            }
        },
        'model-integration': {
            'id': 'model-integration',
            'name': 'Model Integration',
            'data': []
        }
    }

    json_data = json.dumps(sheets_data)
    compressed = zlib.compress(json_data.encode('utf-8'), level=9)  # Ensure maximum compression
    compressed_b64 = base64.b64encode(compressed).decode('utf-8')
    return compressed_b64

@bp.route('/<project_name>/<version_name>/ai-assistant', methods=['POST'])
def ai_assistant(project_name, version_name):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    instructions = request.json['instructions']
    sales_data = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/sales_data.csv', low_memory=False)
    columns = sales_data.columns.tolist()
    # make a call to openai
    system_prompt = '''You are a helpful assistant that can help me with my segmentation. 
                        I have a dataset with the following columns: ''' + ", ".join(columns) + '''
                        I want to create a segmentation for this dataset. 
                        I have the following instructions from the user: ''' + instructions + '''
                        You will give me a json object that contains a python code that will create a segmentation for this dataset, then will return a echarts option object.
                        Only return the code, do not include any other text or comments.
                        sample echarts option object: option={title:{text:'Maleandfemaleheightandweightdistribution',left:'center',top:'10px',textStyle:{fontSize:14,fontWeight:'bold',fontFamily:'Barlow,sans-serif',color:'#1b645b'}},grid:{left:'3%',right:'7%',bottom:'7%',containLabel:true},tooltip:{//trigger:'axis',showDelay:0,formatter:function(params){if(params.value.length>1){return(params.seriesName+':<br/>'+params.value[0]+'cm'+params.value[1]+'kg');}else{return(params.seriesName+':<br/>'+params.name+':'+params.value+'kg');}},axisPointer:{show:true,type:'cross',lineStyle:{type:'dashed',width:1}}},toolbox:{feature:{dataZoom:{},brush:{type:['rect','polygon','clear']}}},brush:{},legend:{data:['Female','Male'],left:'center',bottom:10},xAxis:[{type:'value',scale:true,axisLabel:{formatter:'{value}cm'},splitLine:{show:false}}],yAxis:[{type:'value',scale:true,axisLabel:{formatter:'{value}kg'},splitLine:{show:false}}],series:[{name:'Female',type:'scatter',emphasis:{focus:'series'},//prettier-ignoredata: femaleData,markArea:{silent:true,itemStyle:{color:'transparent',borderWidth:1,borderType:'dashed'},data:[[{name:'FemaleDataRange',xAxis:'min',yAxis:'min'},{xAxis:'max',yAxis:'max'}]]},markPoint:{data:[{type:'max',name:'Max'},{type:'min',name:'Min'}]},markLine:{lineStyle:{type:'solid'},data:[{type:'average',name:'AVG'},{xAxis:160}]}},{name:'Male',type:'scatter',emphasis:{focus:'series'},data:maleData,markArea:{silent:true,itemStyle:{color:'transparent',borderWidth:1,borderType:'dashed'},data:[[{name:'MaleDataRange',xAxis:'min',yAxis:'min'},{xAxis:'max',yAxis:'max'}]]},markPoint:{data:[{type:'max',name:'Max'},{type:'min',name:'Min'}]},markLine:{lineStyle:{type:'solid'},data:[{type:'average',name:'Average'},{xAxis:170}]}}]};
                        Your code should generate an option similar to this. but instead of male and female, there will be segment names that you will generate. 
                        femaleData and maleData will be replaced with the data generated by the code. and options should be updated accordingly.
                        Your response should be something like this:
                        {
                            'code':  '```python
                            def create_segmentation(data):
                                # code should make segmentation here.
                                # the code should create options for a echarts chart
                                return options
                            ```',
                            'explanation': 'I have created a segmentation for you. (anything you want to say related to the segmentation)'
                        }
                        '''
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": system_prompt}],
        temperature=0.5,
        max_tokens=1000
    )

    return jsonify({'status': 'success', 'response': response.choices[0].message.content})


