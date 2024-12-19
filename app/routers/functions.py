import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import itertools
import json
#suppress warnings
import warnings
import time
import os
warnings.filterwarnings("ignore")

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

sample_config = {
  "project_name": 5,
  "version_name": 32,
  "data_file_path": "cloud/5/32/input/template.xlsx",
  "this_year": 2021,
  "breakdown_params": {
    "IAM": "SUBSCRIPTION",
    "IGA": "SUBSCRIPTION",
    "LOG": "SUBSCRIPTION",
    "ADMS": "SUBSCRIPTION",
    "PAM": "SUBSCRIPTION",
    "OID IAM": "SUBSCRIPTION",
    "Provisioning and Automation": "SUBSCRIPTION",
    "Identity Governance": "SUBSCRIPTION",
    "Log Management": "SUBSCRIPTION",
    "User Account Management": "SUBSCRIPTION",
    "SaaS One Identity": "SUBSCRIPTION",
    "IAM Legacy": "SUBSCRIPTION"
  },
  "percentile": 0.7,
  "quartile_function": "QUARTILE.EXC",
  "breakdown_column": "Product Super Family",
  "cohort_columns": "Common Industry",
  "minimum_sample_size": 40,
  "aggregation_variable": "REVENUE",
  "revenue_buckets": [
    -np.inf,
    0,
    26000000,
    91000000,
    400000000,
    2000000000,
    13000000000,
    np.inf
  ],
  "spend_buckets": [-np.inf, 0, 730, 4700, 13000, 29000, 78000, np.inf]
}

def round_to_n_significant_digits(num, n):
    if num == 0 or np.isnan(num) or np.isinf(num):
        return num
    factor = 10**(int(np.floor(np.log10(abs(num)))) - n + 1)
    rounded_num = round(num / factor) * factor
    return rounded_num

def create_buckets(data, n):
    data = data.astype(str).replace('NO DATA', '-1').astype(float)
    data = data[(data > 0) & data.notnull()]
    # if there are less than n unique values, we need to fix the buckets
    unique_values = data.unique()
    unique_values = np.sort(unique_values)
    if len(unique_values) == n:
        data = data[data > 0]
        n = len(unique_values)
        quantiles = [-np.inf, 0]
        for i in range(n):
            if i < n - 1:
                quantiles.append((unique_values[i] + unique_values[i+1])/2)
            else:
                quantiles.append(np.inf)
    else:
        quantiles = [-np.inf, 0] + data.quantile([i/n for i in range(1, n)]).tolist() + [np.inf]
        quantiles = [round_to_n_significant_digits(q, 2) for q in quantiles]
    return quantiles

def excel_quartile_exc(data, q):
    if not 0 <= q <= 1:
        raise ValueError("q should be between 0 and 1")
    data = np.sort(data)
    n = len(data)
    if n < 3:
        return None
    pos = q * (n + 1) - 1
    if pos < 0:
        return data[0]
    elif pos >= n - 1:
        return data[-1]
    else:
        lower = np.floor(pos).astype(int)
        upper = np.ceil(pos).astype(int)
        return data[lower] + (data[upper] - data[lower]) * (pos - lower)

def beautify(num):
    # K M B T Q
    num = float(num)
    if num < 1000:
        s = str(num)
    elif num < 1000000:
        s = str(num/1000) + 'K'
    elif num < 1000000000:
        s = str(num/1000000) + 'M'
    elif num < 1000000000000:
        s = str(num/1000000000) + 'B'
    else:
        s = str(num)    
    return s.replace('.0', '')

def preprocess_data(config):
    excel_file_path = config['data_file_path']
    sales_data = pd.read_excel(excel_file_path, sheet_name='sales_data')
    if 'Asset  Value' in sales_data.columns:
        sales_data = sales_data.rename(columns={'Asset  Value': 'Asset Value'})
    sales_data = sales_data[sales_data['Asset Value'] != 0]
    product_lookup = pd.read_excel(excel_file_path, sheet_name='product_lookup')
    product_lookup = product_lookup.drop_duplicates(subset='Product Name', keep='first')
    industry_lookup = pd.read_excel(excel_file_path, sheet_name='industry_lookup')
    geo_lookup = pd.read_excel(excel_file_path, sheet_name='geo_lookup')
    customer_lookup = pd.read_excel(excel_file_path, sheet_name='customer_lookup')
    customer_lookup = customer_lookup.drop_duplicates(subset='Account ID', keep='first')

    # merge customer lookup with industry and geo lookup
    customer_lookup = pd.merge(customer_lookup, industry_lookup, on='Industry', how='left')
    customer_lookup = pd.merge(customer_lookup, geo_lookup, on='Geo', how='left')
    # merge sales data with product lookup to get the product family
    sales_data = pd.merge(sales_data, product_lookup, on='Product Name', how='left')
    sales_data = pd.merge(sales_data, customer_lookup, on='Account ID', how='left')
    sales_data.loc[pd.isnull(sales_data['Common Industry']), 'Common Industry'] = 'Other'
    sales_data.loc[pd.isnull(sales_data['Common Geo']), 'Common Geo'] = 'Other'
    sales_data.loc[pd.isnull(sales_data['Segment']), 'Segment'] = 'Other'
    # create multiple cohort columns:
    cohort_set = sorted(['Common Industry', 'Common Geo', 'Segment'])
    for i in range(2, len(cohort_set)+1):
        for subset in itertools.combinations(cohort_set, i):
            sales_data[' - '.join(subset)] = sales_data[list(subset)].apply(lambda row: ' - '.join([str(v) for v in row.values]), axis=1)

    # strip leading and trailing spaces from all columns
    for col in ['Product Name', 'Product Family', 'Product Super Family', 'Common Industry', 'Common Geo', 'Segment', 'Account Name']:
        sales_data[col].fillna('Empty', inplace=True)
        sales_data[col] = sales_data[col].astype(str).str.strip().str.replace(r'[^a-zA-Z0-9\s]', '-', regex=True)
    
    # TODO: if there are not matching products, user should be warned


    # filter non-zero asset value assets
    # datetime conversion. check if 'Asset Start Date' and 'Asset End Date' are in the correct format
    # only numbers and 'NO DATA' is accepted in revenue column and asset value column
    # product names, product family, industry, geo, customer names, and account names should not have any special characters
    # check if there are any missing values in the columns
    
    sales_data = sales_data[sales_data['Asset Value'] != 0]
    # if sales_data['Asset Value'] is integer.. convert it to date:
    if pd.api.types.is_integer_dtype(sales_data['Asset Start Date']):
        sales_data['Asset Start Date'] = pd.to_datetime(sales_data['Asset Start Date'], unit='D', origin='1899-12-30')
        sales_data['Asset End Date'] = pd.to_datetime(sales_data['Asset End Date'], unit='D', origin='1899-12-30')
    else:
        sales_data['Asset Start Date'] = pd.to_datetime(sales_data['Asset Start Date'], errors='coerce')
        sales_data['Asset End Date'] = pd.to_datetime(sales_data['Asset End Date'], errors='coerce')
    
    return sales_data, product_lookup, industry_lookup, geo_lookup, customer_lookup

def create_unique_account_list(sales_data, config, breakdown_list):
    unique_account_list = sales_data.groupby('Account ID', as_index=False).agg({'ARR_OR_BOOKINGS': 'first', 'Account Name': 'first', 'ACCOUNT_TOTAL_REVENUE': 'first', config['cohort_columns']: 'first', 'Common Industry': 'first', 'Common Geo': 'first', 'Segment': 'first'})
    sales_data['year'] = sales_data['Asset End Date'].dt.year
    # check if config['this_year'] is in the sales data:
    if config['this_year'] not in sales_data['year'].unique():
        # then use the one year before last year in the sales data
        config['this_year'] = sales_data['year'].max() - 1
    date_filter_end = {year: sales_data['Asset End Date'] >= datetime(year, 12, 31) for year in [config['this_year']-1, config['this_year']]}
    date_filter_start = {year: sales_data['Asset Start Date'] <= datetime(year, 12, 31) for year in [config['this_year']-1, config['this_year']]}


    for year in [ config['this_year']-1, config['this_year']]:
        for breakdown in breakdown_list:
            filtered_data = sales_data[(sales_data[config['breakdown_column']] == breakdown) & date_filter_end[year] & date_filter_start[year]]\
                            .groupby(['Account ID'], as_index=False).agg({'Asset Value': 'sum'}).rename(columns={'Asset Value': f'{year}_{breakdown}'})
            unique_account_list = pd.merge( unique_account_list, filtered_data, on='Account ID', how='left')
    unique_account_list['Current Year Spend'] = unique_account_list[[col for col in unique_account_list.columns if str(config['this_year']) in col]].sum(axis=1)
    # create revenue and spend buckets 
    # revenue_buckets = [-np.inf, 0, 20000000, 75000000, 350000000, 1500000000, 10000000000,  np.inf]
    # spend_buckets =  [-np.inf, 0, 1000, 5000, 15000, 30000, 75000, np.inf]
    
    if 'revenue_buckets' in config:
        revenue_buckets = config['revenue_buckets']
        spend_buckets = config['spend_buckets']
    else:
        if len(unique_account_list['ACCOUNT_TOTAL_REVENUE'].unique()) < 6:
            n_buckets = len(unique_account_list['ACCOUNT_TOTAL_REVENUE'].unique())
        else:
            n_buckets = 6
        revenue_buckets = create_buckets(unique_account_list['ACCOUNT_TOTAL_REVENUE'], n_buckets)
        spend_buckets = create_buckets(unique_account_list['Current Year Spend'], n_buckets)

    revenue_buckets_labels = [f'{beautify(revenue_buckets[i])}-{beautify(revenue_buckets[i+1])}' for i in range(len(revenue_buckets)-1)]
    spend_buckets_labels = [f'{beautify(spend_buckets[i])}-{beautify(spend_buckets[i+1])}' for i in range(len(spend_buckets)-1)]
    revenue_buckets_labels[-1] = f'{beautify(revenue_buckets[-2])}+'
    spend_buckets_labels[-1] = f'{beautify(spend_buckets[-2])}+'
    spend_buckets_labels[0] = 'Less than 0'
    revenue_buckets_labels[0] = 'BLANK / NO DATA'
    unique_account_list.loc[unique_account_list['ACCOUNT_TOTAL_REVENUE'] == 0, 'ACCOUNT_TOTAL_REVENUE'] = 1
    # if there are less than 6 unique values in the revenue column, we need to fix the buckets

    unique_account_list['Revenue Bucket'] = pd.cut(unique_account_list['ACCOUNT_TOTAL_REVENUE'].astype(str).replace('NO DATA', '-1').astype(float), bins=revenue_buckets, labels=revenue_buckets_labels, right=False)
    unique_account_list['Revenue Bucket'] = unique_account_list['Revenue Bucket'].astype(str).str.replace('-inf-0', 'BLANK / NO DATA')

    # if spend_buckets does not increase monotically, we need to fix it, add 1 to the last element
    for i in range(1, len(spend_buckets)):
        if spend_buckets[i] <= spend_buckets[i-1]:
            spend_buckets[i] = spend_buckets[i-1] + i

    unique_account_list.loc[unique_account_list['Current Year Spend'] == 0, 'Current Year Spend'] = 1
    print(unique_account_list['Current Year Spend'])
    unique_account_list['Spend Bucket'] = pd.cut(unique_account_list['Current Year Spend'].astype(float), bins=spend_buckets, labels=spend_buckets_labels, right=True)
    unique_account_list['Spend Bucket'] = unique_account_list['Spend Bucket'].astype(str).str.replace('nan', spend_buckets_labels[1])
    return unique_account_list, revenue_buckets_labels, spend_buckets_labels, revenue_buckets, spend_buckets

def create_deal_size_database(unique_account_list, sales_data, config, breakdown_list):
    deal_size_database = unique_account_list[['Account ID', 'Account Name', 'ARR_OR_BOOKINGS', 'ACCOUNT_TOTAL_REVENUE', 'Revenue Bucket', 'Spend Bucket', 'Current Year Spend', config['cohort_columns']]].copy()
    for deal_type in ['PERPETUAL', 'SUBSCRIPTION']:
        for year in [ config['this_year']-1, config['this_year']]:
            date_filter_end = sales_data['Asset End Date'] > datetime(year, 12, 31)
            date_filter_start = sales_data['Asset Start Date'] <= datetime(year, 12, 31)
            for breakdown in breakdown_list:
                breakdown_year_deals = sales_data[(sales_data[config['breakdown_column']] == breakdown) & date_filter_end & date_filter_start]\
                                        .groupby(['Account ID'], as_index=False).agg({deal_type +' $': 'sum'}).rename(columns={deal_type +' $': f'{year}_{breakdown}_{deal_type}'})
                deal_size_database = pd.merge( deal_size_database, breakdown_year_deals, on='Account ID', how='left')
    return deal_size_database

def create_percentiles(deal_size_database, config, revenue_buckets_labels, spend_buckets_labels, breakdown_list):

    def percentile_func(x):
        if config['quartile_function'] == 'QUARTILE.EXC':
                return excel_quartile_exc(x, config['percentile'])
        else:
            return np.percentile(x, config['percentile'])

    def get_percentile_all_cohorts(x):
        valid_data = x[(x != 0) & x.notnull()]
        return percentile_func(valid_data)
    def get_percentile(x):
        valid_data = x[(x != 0) & x.notnull()]
        if len(valid_data) >= minimum_sample_size:
            return percentile_func(valid_data)
        else:
            return np.nan
        
    percentile_calculation_base_year = config['this_year']
    minimum_sample_size = config['minimum_sample_size']
    aggfunc = {f"{percentile_calculation_base_year}_{breakdown}_{deal_type}": get_percentile_all_cohorts for deal_type in ['PERPETUAL', 'SUBSCRIPTION'] for breakdown in breakdown_list}
    revenue_all_cohorts = deal_size_database.groupby('Revenue Bucket',as_index=False).agg(aggfunc)
    spend_all_cohorts = deal_size_database.groupby('Spend Bucket',as_index=False).agg(aggfunc)
    deal_size_database['COMBINED_REVENUE_KEY'] = deal_size_database['Revenue Bucket'] + '_' + deal_size_database[config['cohort_columns']]
    deal_size_database['COMBINED_SPEND_KEY'] = deal_size_database['Spend Bucket'] + '_' + deal_size_database[config['cohort_columns']]
    # calculate percentiles for each cohort if there are not enough data, use the all cohort percentiles

    aggfunc = {f"{percentile_calculation_base_year}_{breakdown}_{deal_type}": get_percentile for deal_type in ['PERPETUAL', 'SUBSCRIPTION'] for breakdown in breakdown_list}
    aggfunc[config['cohort_columns']] = 'first'
    aggfunc['Revenue Bucket'] = 'first'
    revenue_cohorts = deal_size_database.groupby('COMBINED_REVENUE_KEY',as_index=False).agg(aggfunc)
    aggfunc['Spend Bucket'] = 'first'
    spend_cohorts = deal_size_database.groupby('COMBINED_SPEND_KEY',as_index=False).agg(aggfunc)

    cols = [f"{percentile_calculation_base_year}_{breakdown}_{deal_type}" for deal_type in ['PERPETUAL', 'SUBSCRIPTION'] for breakdown in breakdown_list]
    revenue_cohorts = revenue_cohorts.merge(revenue_all_cohorts[cols+['Revenue Bucket']], on='Revenue Bucket', suffixes=('', '_all_cohorts_revenue'))
    spend_cohorts = spend_cohorts.merge(spend_all_cohorts[cols+['Spend Bucket']], on='Spend Bucket', suffixes=('', '_all_cohorts_spend'))

    cols = [f"{percentile_calculation_base_year}_{breakdown}_{deal_type}" for deal_type in ['PERPETUAL', 'SUBSCRIPTION'] for breakdown in breakdown_list]

    for col in cols:
        revenue_cohorts[col] = revenue_cohorts[col].fillna(revenue_cohorts[f"{col}_all_cohorts_revenue"])
        spend_cohorts[col] = spend_cohorts[col].fillna(spend_cohorts[f"{col}_all_cohorts_spend"])

    revenue_cohorts.drop([f"{col}_all_cohorts_revenue" for col in cols], axis=1, inplace=True)
    spend_cohorts.drop([f"{col}_all_cohorts_spend" for col in cols], axis=1, inplace=True)

    revenue_cohorts = revenue_cohorts.rename(columns={f'{percentile_calculation_base_year}_{breakdown}_{deal_type}':
                                                       f'{breakdown}_{deal_type}' for deal_type in ['PERPETUAL', 'SUBSCRIPTION'] for breakdown in breakdown_list})
    spend_cohorts = spend_cohorts.rename(columns={f'{percentile_calculation_base_year}_{breakdown}_{deal_type}':
                                                         f'{breakdown}_{deal_type}' for deal_type in ['PERPETUAL', 'SUBSCRIPTION'] for breakdown in breakdown_list})

    return revenue_cohorts, spend_cohorts

def create_opportunity_database(deal_size_database, unique_account_list, config, revenue_cohorts, spend_cohorts, breakdown_list):
    opportunity_database = deal_size_database[['Account ID', 'Account Name', 'ARR_OR_BOOKINGS', 'ACCOUNT_TOTAL_REVENUE', 'Revenue Bucket', 'Spend Bucket', 'Current Year Spend', config['cohort_columns']]].copy()
    opportunity_database = opportunity_database.merge(unique_account_list[[col for col in unique_account_list.columns if str(config['this_year']) in col] + ['Account ID']].fillna(0), on='Account ID', how='left')
    opportunity_database = opportunity_database.merge(revenue_cohorts, on=['Revenue Bucket', config['cohort_columns']], how='left')

    for breakdown in breakdown_list:
        for deal_type in ['PERPETUAL', 'SUBSCRIPTION']:
            opportunity_database[breakdown + '_' + deal_type + '_' + 'REVENUE'] = (opportunity_database[breakdown + '_' + deal_type] * (opportunity_database[str(config['this_year']) + '_' + breakdown] <= 0).astype(int)).fillna(0)
            opportunity_database.drop(columns=[breakdown + '_' + deal_type], axis=1, inplace=True)

    opportunity_database = opportunity_database.merge(spend_cohorts, on=['Spend Bucket', config['cohort_columns']], how='left')
    for breakdown in breakdown_list:
        for deal_type in ['PERPETUAL', 'SUBSCRIPTION']:
            opportunity_database[breakdown + '_' + deal_type + '_' + 'SPEND'] = (opportunity_database[breakdown + '_' + deal_type] * (opportunity_database[str(config['this_year']) + '_' + breakdown] <= 0).astype(int)).fillna(0)
            opportunity_database.drop(columns=[breakdown + '_' + deal_type], axis=1, inplace=True)

    for breakdown in breakdown_list:
        for deal_type in ['PERPETUAL', 'SUBSCRIPTION']:
            opportunity_database[breakdown + '_' + deal_type + '_' + 'AVERAGE'] = (opportunity_database[breakdown + '_' + deal_type + '_' + 'REVENUE'] + opportunity_database[breakdown + '_' + deal_type + '_' + 'SPEND']) / 2

    for breakdown in breakdown_list:
        column_name = breakdown + '_' + config['breakdown_params'][breakdown] + '_' + config['aggregation_variable']
        opportunity_database['OPPORTUNITY_VALUE_' + breakdown] = opportunity_database[column_name]
    opportunity_database.drop([config['cohort_columns']], axis=1, inplace=True)
    return opportunity_database

def create_up_sell_database(deal_size_database, unique_account_list, config, revenue_cohorts, spend_cohorts, breakdown_list):
    up_sell_database = deal_size_database[['Account ID', 'Account Name', 'ARR_OR_BOOKINGS', 'ACCOUNT_TOTAL_REVENUE', 'Revenue Bucket', 'Spend Bucket', 'Current Year Spend', config['cohort_columns']]].copy()
    up_sell_database = up_sell_database.merge(unique_account_list[[col for col in unique_account_list.columns if str(config['this_year']) in col] + ['Account ID']].fillna(0), on='Account ID', how='left')
    up_sell_database = up_sell_database.merge(revenue_cohorts, on=['Revenue Bucket', config['cohort_columns']], how='left')

    # Key difference from cross-sell: We only look at accounts that DO have the product
    for breakdown in breakdown_list:
        for deal_type in ['PERPETUAL', 'SUBSCRIPTION']:
            # Only calculate opportunity when account has the product (> 0) and the percentile value is higher than current spend
            up_sell_database[breakdown + '_' + deal_type + '_' + 'REVENUE'] = (
                up_sell_database[breakdown + '_' + deal_type] * 
                (up_sell_database[str(config['this_year']) + '_' + breakdown] > 0).astype(int) *  # Has product
                (up_sell_database[breakdown + '_' + deal_type] > up_sell_database[str(config['this_year']) + '_' + breakdown]).astype(int)  # Percentile > current spend
            ).fillna(0)
            up_sell_database.drop(columns=[breakdown + '_' + deal_type], axis=1, inplace=True)

    up_sell_database = up_sell_database.merge(spend_cohorts, on=['Spend Bucket', config['cohort_columns']], how='left')
    for breakdown in breakdown_list:
        for deal_type in ['PERPETUAL', 'SUBSCRIPTION']:
            # Same logic for spend-based calculations
            up_sell_database[breakdown + '_' + deal_type + '_' + 'SPEND'] = (
                up_sell_database[breakdown + '_' + deal_type] * 
                (up_sell_database[str(config['this_year']) + '_' + breakdown] > 0).astype(int) *
                (up_sell_database[breakdown + '_' + deal_type] > up_sell_database[str(config['this_year']) + '_' + breakdown]).astype(int)
            ).fillna(0)
            up_sell_database.drop(columns=[breakdown + '_' + deal_type], axis=1, inplace=True)

    # Calculate average of revenue and spend based opportunities
    for breakdown in breakdown_list:
        for deal_type in ['PERPETUAL', 'SUBSCRIPTION']:
            up_sell_database[breakdown + '_' + deal_type + '_' + 'AVERAGE'] = (
                up_sell_database[breakdown + '_' + deal_type + '_' + 'REVENUE'] + 
                up_sell_database[breakdown + '_' + deal_type + '_' + 'SPEND']
            ) / 2

    # Select final opportunity value based on breakdown parameters
    for breakdown in breakdown_list:
        column_name = breakdown + '_' + config['breakdown_params'][breakdown] + '_' + config['aggregation_variable']
        up_sell_database['OPPORTUNITY_VALUE_' + breakdown] = up_sell_database[column_name]

    up_sell_database.drop([config['cohort_columns']], axis=1, inplace=True)
    return up_sell_database


#### STEP 10 ####
# create 10.1 fact book based on breakdown_list 
def create_factbook(project_name, version_name, date, breakdown_column, cohort_column, filter_column=None, filter_value=None, bundling_filters={}, selected_breakdown=None, requestor=None, bundling_table_type=None):
    sales_data = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/sales_data.csv', low_memory=False)
    sales_data['Asset Start Date'] = pd.to_datetime(sales_data['Asset Start Date'])
    sales_data['Asset End Date'] = pd.to_datetime(sales_data['Asset End Date'])
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    breakdown_list = sales_data[breakdown_column].unique()
    unique_account_list, revenue_buckets_labels, spend_buckets_labels, revenue_buckets, spend_buckets = create_unique_account_list(sales_data, config, breakdown_list)

    cohort_lists = {}
    for col in ['Revenue Bucket', 'Spend Bucket', 'Common Industry', 'Common Geo', 'Segment']:
        cohort_lists[col] = ['All'] + unique_account_list[col].unique().tolist()

    #breakdown_list = sales_data['Product FAMILY'].unique().tolist()
    factbook_database = unique_account_list[['Account ID', 'Account Name', 'ARR_OR_BOOKINGS', 'ACCOUNT_TOTAL_REVENUE', 'Revenue Bucket', 'Spend Bucket', 'Current Year Spend', 'Common Industry', 'Segment','Common Geo']].copy()
    for breakdown in breakdown_list:
        breakdown_fact = sales_data[sales_data[breakdown_column] == breakdown]
        breakdown_fact = breakdown_fact[breakdown_fact['Asset Start Date'] <= date]
        breakdown_fact = breakdown_fact[breakdown_fact['Asset End Date'] > date]
        breakdown_fact = breakdown_fact.groupby(['Account ID'], as_index=False).agg({'Asset Value': 'sum'}).rename(columns={'Asset Value': f'{breakdown}'})
        factbook_database = pd.merge( factbook_database, breakdown_fact.round(0), on='Account ID', how='left')
    factbook_database['Total'] = factbook_database[[col for col in factbook_database.columns if any(name in col for name in breakdown_list)]].sum(axis=1).round(0)
    # create ARR Sum Row
    total_row = factbook_database[[col for col in factbook_database.columns if any(name in col for name in breakdown_list)]+['Total']].sum()
    total_row[cohort_column] = 'Total'
    # create no of customers row
    customer_count_row = (factbook_database[[col for col in factbook_database.columns if any(name in col for name in breakdown_list)]]>0).sum()
    customer_count_row[cohort_column] = 'Total Customers'
    
    data_cube = factbook_database.copy()
    # data_cube.loc[-1] = total_row
    # data_cube.loc[-2] = customer_count_row
    data_cube = data_cube.sort_index().reset_index(drop=True)
    # count the number of products sold to each customer
    data_cube['product_count'] = (data_cube[[col for col in data_cube.columns if any(name in col for name in breakdown_list)]] > 0).sum(axis=1)
    # total row and customer count row should be at the top of dataframe
    data_cube.fillna(0, inplace=True)

    if filter_column:
        filter_values = ['All'] + factbook_database[filter_column].unique().tolist()
    else:
        filter_values = ['All']

    if requestor == 'data_cube':
        return breakdown_list, data_cube, filter_values, None, None, None, None, None

    # create 10.02 Fact Pack Viz book based on breakdown_list

    selected_columns = [col for col in factbook_database.columns if any(name in col for name in breakdown_list)]
    summary_table = factbook_database.groupby([cohort_column], as_index = False)[selected_columns].sum()

    total_asset_value = sum(factbook_database[selected_columns].sum())
    total_row = factbook_database[selected_columns].sum(axis=0).to_frame().T
    ARR_row = ((total_row/total_asset_value)*100).round(2)
    customer_count_row = (factbook_database[selected_columns]>0).sum().to_frame().T
    customer_total_count = (factbook_database['Total']>0).sum()
    customer_percentage = ((customer_count_row/customer_total_count)*100).round(2)
    USD_per_customer = (total_row/customer_count_row).round(0)

    total_row[cohort_column] = 'Total'
    ARR_row[cohort_column] = 'ARR of Total'
    customer_count_row[cohort_column] = 'Total Customers'
    customer_percentage[cohort_column] = 'Percentage of Total Customers'
    USD_per_customer[cohort_column] = 'USD_per_customer'
    # summary_table = pd.concat([summary_table, total_row, ARR_row, customer_count_row, customer_percentage, USD_per_customer], axis=0)
    # summary_table = summary_table.reset_index(drop=True)

    if requestor == 'arrs':
        return breakdown_list, data_cube, filter_values, summary_table, None, None, None, None

    #create 10.03 Pareto Chart Vis
    columns_used = ['Account ID', 'Account Name', 'ARR_OR_BOOKINGS',
        'ACCOUNT_TOTAL_REVENUE', 'Revenue Bucket', 'Spend Bucket',
        'Current Year Spend', 'Common Industry', 'Segment',
        'Common Geo',  f'Total']
    
    pareto_df = factbook_database[columns_used].copy()
    if filter_column and filter_value and filter_value != 'All':
        pareto_df = pareto_df[pareto_df[filter_column] == filter_value]
    
    pareto_df = pareto_df.sort_values(by= f'Total', ascending= False)
    pareto_df['Percentage'] = (pareto_df[f'Total'] / pareto_df[f'Total'].sum()) * 100

    # #pareto by cohort general 
    # pareto_by_cohort_df = pareto_df.groupby([cohort_column], as_index = False)[f'Total'].sum()
    # pareto_by_cohort_df = pareto_by_cohort_df.sort_values(by= f'Total', ascending= False)
    # pareto_by_cohort_df['Percentage'] = (pareto_by_cohort_df[f'Total'] / pareto_by_cohort_df[f'Total'].sum()) * 100

    #pareto by cohort by Account ID & other columns

    pareto_by_cohort_account_df = pareto_df.groupby(columns_used[:-1], as_index = False)[f'Total'].sum()
    pareto_by_cohort_account_df = pareto_by_cohort_account_df.sort_values(by= f'Total', ascending= False)
    pareto_by_cohort_account_df['Percentage'] = (pareto_by_cohort_account_df[f'Total'] / pareto_by_cohort_account_df[f'Total'].sum()) * 100
    pareto_by_cohort_account_df.reset_index(drop=True, inplace=True)

    if requestor == 'pareto_analysis':
        return breakdown_list, data_cube, filter_values, summary_table, pareto_by_cohort_account_df, None, None, None

    #10.4 Attach rates
    attach_df = pd.DataFrame(columns = [breakdown_column] + selected_columns)
    attach_rate = pd.DataFrame(columns = [breakdown_column] + selected_columns)
    ar_base = factbook_database.copy()
    if filter_column and filter_value and filter_value != 'All':
        ar_base = ar_base[ar_base[filter_column] == filter_value]
        
    for breakdown in breakdown_list:
        breakdown_fact_attach = ar_base.copy()
        breakdown_fact_attach = breakdown_fact_attach[breakdown_fact_attach[f'{breakdown}']>0]
        
        attach_counts = breakdown_fact_attach[selected_columns].gt(0).sum()
        max_count = attach_counts.max()
        attach_percent = ((attach_counts/max_count) * 100).to_frame().T

        #in case of counts required to show
        attach_counts[breakdown_column] = breakdown
        attach_df = pd.concat([attach_df, attach_counts], axis=0)

        #end table attach rate
        attach_percent[breakdown_column] = breakdown
        attach_rate = pd.concat([attach_rate, attach_percent], axis=0)

    
    attach_rate = attach_rate.round(2).reset_index(drop=True)

    if requestor == 'attach_rates':
        return breakdown_list, data_cube, filter_values, summary_table, pareto_by_cohort_account_df, attach_rate.fillna(0), None, None
    
    # 10.5 Bundling 
    # for a selected date and breakdown column, calculate the number of sold breakdowns for each account.
    # then count the number of accounts where number of sold breakdown == number, and cohort equals to the selected cohort
    
    for key in bundling_filters.keys():
        if bundling_filters[key] != 'All':
            data_cube = data_cube[data_cube[key] == bundling_filters[key]]

    if selected_breakdown not in breakdown_list:
        selected_breakdown = breakdown_list[0]
    numerator_table = {}    
    for i in range(1, len(breakdown_list)+1):
        temp_cube = data_cube[data_cube['product_count'] == i]
        temp_cube = temp_cube[~temp_cube[cohort_column].isin(['Total', 'Total Customers'])]
        numerator_table[str(i)] = {}
        for breakdown in breakdown_list:
            number = temp_cube[(temp_cube[breakdown] > 0) & (temp_cube[selected_breakdown] > 0)].shape[0]
            numerator_table[str(i)][breakdown] = number

    numerator_table['0'] = {}
    for breakdown in breakdown_list:   
        temp_cube = data_cube[data_cube['product_count'] > 0]
        temp_cube = temp_cube[~temp_cube[cohort_column].isin(['Total', 'Total Customers'])]
        numerator_table['0'][breakdown] = temp_cube[(temp_cube[breakdown] > 0) & (temp_cube[selected_breakdown] == 0)].shape[0]


    s = 0
    for breakdown in breakdown_list:
        s += numerator_table['0'][breakdown]

    bundling_table = {}
    for i in range(0, len(breakdown_list)+1):
        bundling_table[str(i)] = {}
        for breakdown in breakdown_list:
            if i == 0:
                if s == 0:
                    bundling_table[str(i)][breakdown] = 0
                else:
                    bundling_table[str(i)][breakdown] = numerator_table[str(i)][breakdown] / s
            else:
                if  numerator_table[str(i)][selected_breakdown] == 0:
                    bundling_table[str(i)][breakdown] = 0
                else:
                    bundling_table[str(i)][breakdown] = numerator_table[str(i)][breakdown] / numerator_table[str(i)][selected_breakdown]
    
    bundling_table = pd.DataFrame(bundling_table)
    numerator_table = pd.DataFrame(numerator_table)

    for i in range(1, len(breakdown_list)+1):
        s = 0
        for breakdown in breakdown_list:
            s += numerator_table[str(i)][breakdown]
        if s == 0:
            del bundling_table[str(i)]
    if bundling_table_type == 'numerators':
        bundling_table = numerator_table

    return breakdown_list, data_cube, filter_values, summary_table, pareto_by_cohort_account_df, attach_rate.fillna(0), bundling_table.fillna(0), cohort_lists

#### STEP 8 ####
# pricing build:
# create 8.1 pricing build based on breakdown_list
def create_customer_asp(project_name, version_name, date, minimum_seats, percentile_cohort, percentile_filters, min_sample_size):
    # create a table where each row is identified by a customer and sku
    sales_data = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/sales_data.csv', low_memory=False)
    sales_data['PPQ'] = sales_data['Asset Value'] / sales_data['License Quantity']
    sales_data = sales_data[sales_data['Asset Start Date'] <= date]
    sales_data = sales_data[sales_data['Asset End Date'] > date]

    pricing_build = sales_data.groupby(['Account ID', 'Product Name'], as_index=False).agg({'PPQ': 'mean', 'License Quantity': 'sum', 'Asset Value': 'sum', 'Product Family': 'first', 'Product Super Family': 'first'}).rename(columns={'PPQ': 'ASP', 'License Quantity': 'Total Seats', 'Asset Value': 'Total Value'})
    pricing_build['ASP'] = pricing_build['Total Value'] / pricing_build['Total Seats']
    # get unique_account_list
    unique_account_list = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/unique_account_list.csv', low_memory=False)
    unique_account_list = unique_account_list[['Account ID', 'Common Industry', 'Common Geo', 'Segment', 'Revenue Bucket', 'Spend Bucket']]
    pricing_build = pd.merge(pricing_build, unique_account_list, on='Account ID', how='left')
    pricing_build_original = pricing_build.copy()
    cohort_lists = {}
    for col in ['Revenue Bucket', 'Spend Bucket', 'Common Industry', 'Common Geo', 'Segment']:
        cohort_lists[col] = ['All'] + pricing_build[col].unique().tolist()
    for col in ['Product Family', 'Product Super Family']:
        cohort_lists[col] = ['All'] + sales_data[col].unique().tolist()

    pricing_build = pricing_build[pricing_build['Total Seats'] > minimum_seats]

    asp_percentile_table = {}
    licence_quantity_percentile_table = {}
    sample_size_table = {}
    arr_filtered_table = {}
    arr_unfiltered_table = {}
    # create a table where each row is identified by a cohort:
    for cohort_key in pricing_build[percentile_cohort].unique():
        # calculate 25th 50th and 75th percentile for each cohort using the ASP
        cohort_data = pricing_build[pricing_build[percentile_cohort] == cohort_key]
        # apply percentile filters
        for key in percentile_filters.keys():
            if percentile_filters[key] != 'All':
                cohort_data = cohort_data[cohort_data[key] == percentile_filters[key]]
        arr_unfiltered_table[cohort_key] = cohort_data['Total Value'].sum()
        cohort_data = cohort_data[cohort_data['Total Seats'] > minimum_seats]
        cohort_data = cohort_data[cohort_data['ASP'] > 0]
        arr_filtered_table[cohort_key] = cohort_data['Total Value'].sum()
        # calculate percentiles
        asp_percentile_table[cohort_key] = {}
        # implement excel quartile.inc function
        asp_percentile_table[cohort_key]['25th'] = cohort_data['ASP'].quantile(0.25)
        asp_percentile_table[cohort_key]['50th'] = cohort_data['ASP'].quantile(0.5)
        asp_percentile_table[cohort_key]['75th'] = cohort_data['ASP'].quantile(0.75)
        licence_quantity_percentile_table[cohort_key] = {}
        licence_quantity_percentile_table[cohort_key]['25th'] = cohort_data['Total Seats'].quantile(0.25)
        licence_quantity_percentile_table[cohort_key]['50th'] = cohort_data['Total Seats'].quantile(0.5)
        licence_quantity_percentile_table[cohort_key]['75th'] = cohort_data['Total Seats'].quantile(0.75)
        sample_size_table[cohort_key] = cohort_data.shape[0]
        if cohort_data.shape[0] < min_sample_size:
            asp_percentile_table[cohort_key]['25th'] = 'N/A'
            asp_percentile_table[cohort_key]['50th'] = 'N/A'
            asp_percentile_table[cohort_key]['75th'] = 'N/A'
            licence_quantity_percentile_table[cohort_key]['25th'] =  'N/A'
            licence_quantity_percentile_table[cohort_key]['50th'] =  'N/A'
            licence_quantity_percentile_table[cohort_key]['75th'] = 'N/A'
    
    return cohort_lists, pricing_build, asp_percentile_table, licence_quantity_percentile_table, sample_size_table, arr_filtered_table, arr_unfiltered_table

def create_asp_cohorts(project_name, version_name, date, breakdown_column, cohort_columns, minimum_sample_size, bucket_percentile, minimum_seats):
    sales_data = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/sales_data.csv', low_memory=False)
    sales_data['PPQ'] = sales_data['Asset Value'] / sales_data['License Quantity']
    sales_data = sales_data[sales_data['Asset Start Date'] <= date]
    sales_data = sales_data[sales_data['Asset End Date'] > date]
    breakdown_list = sales_data[breakdown_column].unique().tolist()

    pricing_build = sales_data.groupby(['Account ID', 'Product Name'], as_index=False).agg({'PPQ': 'mean', 'License Quantity': 'sum', 'Asset Value': 'sum', 'Product Family': 'first', 'Product Super Family': 'first'}).rename(columns={'PPQ': 'ASP', 'License Quantity': 'Total Seats', 'Asset Value': 'Total Value'})
    pricing_build['ASP'] = pricing_build['Total Value'] / pricing_build['Total Seats']

    # get unique_account_list
    unique_account_list = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/unique_account_list.csv', low_memory=False)
    unique_account_list = unique_account_list[['Account ID', 'Common Industry', 'Common Geo', 'Segment', 'Revenue Bucket', 'Spend Bucket']]
    pricing_build = pd.merge(pricing_build, unique_account_list, on='Account ID', how='left')
    pricing_build = pricing_build[pricing_build['Total Seats'] > minimum_seats]


    x = pricing_build[pricing_build['Revenue Bucket'] == 'BLANK / NO DATA']
    x = x[x['Common Industry'] == 'Other']
    x = x[x['Product Super Family'] == 'IAM']
    def get_percentile_all_cohorts(x):
        return np.quantile(x[(x > 0) & x.notnull()], bucket_percentile)
    
    def get_percentile(x):
        valid_data = x[(x > 0) & x.notnull()]
        if len(valid_data) >= minimum_sample_size:
            return np.quantile(valid_data, bucket_percentile)
        else:
            return np.nan
    
    revenue_all_cohorts = pricing_build.groupby(['Revenue Bucket', breakdown_column],as_index=False).agg({'ASP': get_percentile_all_cohorts})
    revenue_all_cohorts = revenue_all_cohorts.pivot(index='Revenue Bucket', columns=breakdown_column, values='ASP').reset_index().rename_axis(None, axis=1)

    spend_all_cohorts = pricing_build.groupby(['Spend Bucket', breakdown_column],as_index=False).agg({'ASP': get_percentile_all_cohorts})
    spend_all_cohorts = spend_all_cohorts.pivot(index='Spend Bucket', columns=breakdown_column, values='ASP').reset_index().rename_axis(None, axis=1)

    pricing_build['COMBINED_REVENUE_KEY'] = pricing_build['Revenue Bucket'] + '_' + pricing_build[cohort_columns]
    pricing_build['COMBINED_SPEND_KEY'] = pricing_build['Spend Bucket'] + '_' + pricing_build[cohort_columns]

    aggfunc = {f"ASP": get_percentile}
    aggfunc[cohort_columns] = 'first'
    aggfunc['Revenue Bucket'] = 'first'
    revenue_cohorts = pricing_build.groupby(['COMBINED_REVENUE_KEY', breakdown_column],as_index=False).agg(aggfunc)
    aggfunc['Spend Bucket'] = 'first'
    spend_cohorts = pricing_build.groupby(['COMBINED_SPEND_KEY', breakdown_column],as_index=False).agg(aggfunc)
    revenue_cohorts = revenue_cohorts.pivot(index=['COMBINED_REVENUE_KEY', cohort_columns, 'Revenue Bucket'], columns=breakdown_column, values='ASP').reset_index().rename_axis(None, axis=1)
    spend_cohorts = spend_cohorts.pivot(index=['COMBINED_SPEND_KEY',  cohort_columns, 'Spend Bucket'], columns=breakdown_column, values='ASP').reset_index().rename_axis(None, axis=1)

    cols = [f"{breakdown}" for breakdown in breakdown_list]
    revenue_cohorts = revenue_cohorts.merge(revenue_all_cohorts[cols+['Revenue Bucket']], on='Revenue Bucket', suffixes=('', '_all_cohorts_revenue'))
    spend_cohorts = spend_cohorts.merge(spend_all_cohorts[cols+['Spend Bucket']], on='Spend Bucket', suffixes=('', '_all_cohorts_spend'))

    cols = [f"{breakdown}" for breakdown in breakdown_list]
    for col in cols:
        revenue_cohorts[col] = revenue_cohorts[col].fillna(revenue_cohorts[f"{col}_all_cohorts_revenue"])
        spend_cohorts[col] = spend_cohorts[col].fillna(spend_cohorts[f"{col}_all_cohorts_spend"])

    revenue_cohorts.drop([f"{col}_all_cohorts_revenue" for col in cols], axis=1, inplace=True)
    spend_cohorts.drop([f"{col}_all_cohorts_spend" for col in cols], axis=1, inplace=True)


    revenue_cohorts = revenue_cohorts.melt(id_vars=['COMBINED_REVENUE_KEY', cohort_columns, 'Revenue Bucket'], var_name=breakdown_column, value_name='Revenue ' + str(int(bucket_percentile*100))+'th Percentile ASP')
    spend_cohorts = spend_cohorts.melt(id_vars=['COMBINED_SPEND_KEY', cohort_columns, 'Spend Bucket'], var_name=breakdown_column, value_name='Spend ' +str(int(bucket_percentile*100))+'th Percentile ASP')
    revenue_cohorts.drop(['COMBINED_REVENUE_KEY'], axis=1, inplace=True)
    spend_cohorts.drop(['COMBINED_SPEND_KEY'], axis=1, inplace=True)
    return revenue_cohorts, spend_cohorts


def create_uplift(project_name, version_name, date, breakdown_column, minimum_sample_size, minimum_seats, cohort_columns, revenue_spend_toggle, max_arr_uplift, yield_uplift_toggle, yield_uplift_table):
    sales_data = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/sales_data.csv', low_memory=False)
    sales_data['PPQ'] = sales_data['Asset Value'] / sales_data['License Quantity']
    sales_data = sales_data[sales_data['Asset Start Date'] <= date]
    sales_data = sales_data[sales_data['Asset End Date'] > date]

    pricing_build = sales_data.groupby(['Account ID', 'Product Name'], as_index=False).agg({'PPQ': 'mean', 'License Quantity': 'sum', 'Asset Value': 'sum', 'Product Family': 'first', 'Product Super Family': 'first'}).rename(columns={'PPQ': 'ASP', 'License Quantity': 'Total Seats', 'Asset Value': 'Total Value'})
    pricing_build['ASP'] = pricing_build['Total Value'] / pricing_build['Total Seats']

    unique_account_list = pd.read_csv(f'../cloud/{project_name}/{version_name}/output/unique_account_list.csv', low_memory=False)
    unique_account_list = unique_account_list[['Account ID', 'Account Name',  'Common Industry', 'Common Geo', 'Segment', 'Revenue Bucket', 'Spend Bucket']]
    pricing_build = pd.merge(pricing_build, unique_account_list, on='Account ID', how='left')

    # create a table each row is identified by an account and a product (breakdown column)
    uplift_table = pricing_build.groupby(['Account ID', breakdown_column], as_index=False).agg({'Account Name': 'first', 'Product Family': 'first', 'Common Industry': 'first', 'Common Geo': 'first', 'Segment': 'first', 'Revenue Bucket': 'first', 'Spend Bucket': 'first'})

    median_asp = pricing_build[(pricing_build['ASP'] != 0) & (pricing_build['Total Seats'] > minimum_seats)].groupby(['Account ID', breakdown_column], as_index=False).agg({'ASP': 'median'})
    uplift_table = pd.merge(uplift_table, median_asp, on=['Account ID', breakdown_column], how='left')
    uplift_table['Median ASP'] = uplift_table['ASP']
    uplift_table.drop(['ASP'], axis=1, inplace=True)
    revenue_cohorts_25, spend_cohorts_25 = create_asp_cohorts(project_name, version_name, date, breakdown_column, cohort_columns, minimum_sample_size, 0.25, minimum_seats)
    revenue_cohorts_50, spend_cohorts_50 = create_asp_cohorts(project_name, version_name, date, breakdown_column, cohort_columns, minimum_sample_size, 0.5, minimum_seats)
    revenue_cohorts_75, spend_cohorts_75 = create_asp_cohorts(project_name, version_name, date, breakdown_column, cohort_columns, minimum_sample_size, 0.75, minimum_seats)
    uplift_table = pd.merge(uplift_table, revenue_cohorts_25, on=['Revenue Bucket', cohort_columns, breakdown_column], how='left')
    uplift_table = pd.merge(uplift_table, revenue_cohorts_50, on=['Revenue Bucket', cohort_columns, breakdown_column], how='left')
    uplift_table = pd.merge(uplift_table, revenue_cohorts_75, on=['Revenue Bucket', cohort_columns, breakdown_column], how='left')
    uplift_table = pd.merge(uplift_table, spend_cohorts_25, on=['Spend Bucket', cohort_columns, breakdown_column], how='left')
    uplift_table = pd.merge(uplift_table, spend_cohorts_50, on=['Spend Bucket', cohort_columns, breakdown_column], how='left')
    uplift_table = pd.merge(uplift_table, spend_cohorts_75, on=['Spend Bucket', cohort_columns, breakdown_column], how='left')

    
    uplift_table['Revenue Designated Bucket'] = np.where(uplift_table['Median ASP'] <= uplift_table['Revenue 25th Percentile ASP'], '0-25th', 
        np.where(uplift_table['Median ASP'] <= uplift_table['Revenue 50th Percentile ASP'], '25-50th',
        np.where(uplift_table['Median ASP'] <= uplift_table['Revenue 75th Percentile ASP'], '50-75th',
                  '75+')))
    
    uplift_table['Spend Designated Bucket'] = np.where(uplift_table['Median ASP'] <= uplift_table['Spend 25th Percentile ASP'], '0-25th', 
        np.where(uplift_table['Median ASP'] <= uplift_table['Spend 50th Percentile ASP'], '25-50th',
        np.where(uplift_table['Median ASP'] <= uplift_table['Spend 75th Percentile ASP'], '50-75th',
                  '75+')))
       
    uplift_table['Top of Bucket ASP - Revenue'] = np.where(uplift_table['Revenue Designated Bucket'] == '0-25th', uplift_table['Revenue 25th Percentile ASP'],
        np.where(uplift_table['Revenue Designated Bucket'] == '25-50th', uplift_table['Revenue 50th Percentile ASP'],
        np.where(uplift_table['Revenue Designated Bucket'] == '50-75th', uplift_table['Revenue 75th Percentile ASP'],
                  uplift_table['Revenue 75th Percentile ASP'])))
    
    uplift_table['Top of Bucket ASP - Spend'] = np.where(uplift_table['Spend Designated Bucket'] == '0-25th', uplift_table['Spend 25th Percentile ASP'],
        np.where(uplift_table['Spend Designated Bucket'] == '25-50th', uplift_table['Spend 50th Percentile ASP'],
        np.where(uplift_table['Spend Designated Bucket'] == '50-75th', uplift_table['Spend 75th Percentile ASP'],
                  uplift_table['Spend 75th Percentile ASP'])))
    
    uplift_table['Top of Bucket ASP - Selected'] =  uplift_table['Top of Bucket ASP - ' + revenue_spend_toggle].copy()

    total_licenses = sales_data.groupby(['Account ID', breakdown_column], as_index=False).agg({'License Quantity': 'sum'}).rename(columns={'License Quantity': 'Total Seats'}) 
    uplift_table = pd.merge(uplift_table, total_licenses, on=['Account ID', breakdown_column], how='left')

    uplift_table['Implied ARR'] = uplift_table['Top of Bucket ASP - Selected'] * uplift_table['Total Seats']
    uplift_table.loc[uplift_table['Median ASP'] == 0, 'Implied ARR'] = 0

    total_arr = sales_data.groupby(['Account ID', breakdown_column], as_index=False).agg({'Asset Value': 'sum'}).rename(columns={'Asset Value': 'Current ARR'})
    uplift_table = pd.merge(uplift_table, total_arr, on=['Account ID', breakdown_column], how='left')

    uplift_table['Max ARR Uplift'] = (1 + max_arr_uplift) * uplift_table['Current ARR']
    uplift_table['Possible Uplift'] = (uplift_table['Implied ARR'] - uplift_table['Current ARR'])
    uplift_table['Implied Uplift'] = uplift_table[['Possible Uplift', 'Max ARR Uplift']].min(axis=1)
    uplift_table.loc[uplift_table['Possible Uplift'] < 0, 'Implied Uplift'] = 0
   
    uplift_table['Designated Yield %'] = uplift_table[revenue_spend_toggle +' Designated Bucket'].map(yield_uplift_table)
    uplift_table['Yield Adjusted Uplift'] = uplift_table['Implied Uplift'] * (uplift_table['Designated Yield %'] / 100)

    uplift_table['Selected Uplift'] = uplift_table['Implied Uplift']
    if yield_uplift_toggle:
        uplift_table['Selected Uplift'] = uplift_table['Yield Adjusted Uplift']

    return uplift_table


def runXSQuantModel(config, write_data=True, override_config = True): # while combinations are calculate override will be False
    t = time.time()
    sales_data, product_lookup, industry_lookup, geo_lookup, customer_lookup = get_data(config)
    print('Data loaded:', time.time() - t)
    t = time.time()
    breakdown_list = sales_data[config['breakdown_column']].unique()
    unique_account_list, revenue_buckets_labels, spend_buckets_labels, revenue_buckets, spend_buckets = create_unique_account_list(sales_data, config, breakdown_list)
    # add revenue and spend buckets to the config file
    if 'revenue_buckets' not in config and override_config:
        config['revenue_buckets'] = revenue_buckets
        config['spend_buckets'] = spend_buckets
        try:
            with open(f'../cloud/{config["project_name"]}/{config["version_name"]}/config.json', 'w') as config_file:
                json.dump(config, config_file, cls=NpEncoder)
        except:
            return jsonify({'error': 'Could not write to config file', 'config': config})
    check = False
    for breakdown in breakdown_list:
        if breakdown not in config['breakdown_params']:
            check = True
            config['breakdown_params'][breakdown] = 'SUBSCRIPTION'
    if check and override_config:
        # remove keys that are not in breakdown_list
        config['breakdown_params'] = {key: config['breakdown_params'][key] for key in breakdown_list}
        with open(f'../cloud/{config["project_name"]}/{config["version_name"]}/config.json', 'w') as config_file:
            json.dump(config, config_file, cls=NpEncoder)

    print('Unique account list created:', time.time() - t)
    t = time.time()
    deal_size_database = create_deal_size_database(unique_account_list, sales_data, config, breakdown_list)
    print('Deal size database created:', time.time() - t)
    t = time.time()
    revenue_cohorts, spend_cohorts = create_percentiles(deal_size_database, config, revenue_buckets_labels, spend_buckets_labels, breakdown_list)
    print('Cohorts created:', time.time() - t)
    t = time.time()
    opportunity_database = create_opportunity_database(deal_size_database, unique_account_list, config, revenue_cohorts, spend_cohorts, breakdown_list)
    print('Opportunity database created:', time.time() - t)
    t = time.time()
    up_sell_database = create_up_sell_database(deal_size_database, unique_account_list, config, revenue_cohorts, spend_cohorts, breakdown_list)
    print('Up sell database created:', time.time() - t)

    if write_data:
        unique_account_list.to_csv(f'../cloud/{config["project_name"]}/{config["version_name"]}/output/unique_account_list.csv', index=False)
        deal_size_database.to_csv(f'../cloud/{config["project_name"]}/{config["version_name"]}/output/deal_size_database.csv', index=False)
        revenue_cohorts.to_csv(f'../cloud/{config["project_name"]}/{config["version_name"]}/output/revenue_cohorts.csv', index=False)
        spend_cohorts.to_csv(f'../cloud/{config["project_name"]}/{config["version_name"]}/output/spend_cohorts.csv', index=False)
        opportunity_database.to_csv(f'../cloud/{config["project_name"]}/{config["version_name"]}/output/opportunity_database.csv', index=False)
        up_sell_database.to_csv(f'../cloud/{config["project_name"]}/{config["version_name"]}/output/up_sell_database.csv', index=False)
    else:
        return opportunity_database, up_sell_database


def write_data(config):
    project_name = config['project_name']
    version_name = config['version_name']
    sales_data, product_lookup, industry_lookup, geo_lookup, customer_lookup = preprocess_data(config)
    config['breakdown_params'] = {}
    for breakdown in sales_data[config['breakdown_column']].unique().tolist():
        config['breakdown_params'][breakdown] = 'SUBSCRIPTION'
    # cohort columns, cannot be empty
    if config['cohort_columns'] == '':
        config['cohort_columns'] = 'Common Industry'
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'w') as config_file:
        json.dump(config, config_file, cls=NpEncoder)
    # save the data to the output folder
    base_path = f'../cloud/{project_name}/{version_name}'
    sales_data.to_csv(f'{base_path}/output/sales_data.csv', index=False)
    product_lookup.to_csv(f'{base_path}/output/product_lookup.csv', index=False)
    industry_lookup.to_csv(f'{base_path}/output/industry_lookup.csv', index=False)
    geo_lookup.to_csv(f'{base_path}/output/geo_lookup.csv', index=False)
    customer_lookup.to_csv(f'{base_path}/output/customer_lookup.csv', index=False)

def get_data(config):
    # if data is already processed, return the processed data
    project_name = config['project_name']
    version_name = config['version_name']
    base_path = f'../cloud/{project_name}/{version_name}'
    if os.path.exists(f'{base_path}/output/sales_data.csv'):
        sales_data = pd.read_csv(f'{base_path}/output/sales_data.csv', low_memory=False)
        product_lookup = pd.read_csv(f'{base_path}/output/product_lookup.csv', low_memory=False)
        industry_lookup = pd.read_csv(f'{base_path}/output/industry_lookup.csv', low_memory=False)
        geo_lookup = pd.read_csv(f'{base_path}/output/geo_lookup.csv', low_memory=False)
        customer_lookup = pd.read_csv(f'{base_path}/output/customer_lookup.csv', low_memory=False)
        sales_data['Asset Start Date'] = pd.to_datetime(sales_data['Asset Start Date'], errors='coerce')
        sales_data['Asset End Date'] = pd.to_datetime(sales_data['Asset End Date'], errors='coerce')
        return sales_data, product_lookup, industry_lookup, geo_lookup, customer_lookup

def get_config(project_name, version_name):
    with open(f'../cloud/{project_name}/{version_name}/config.json', 'r') as config_file:
        config = json.load(config_file)
    return config
