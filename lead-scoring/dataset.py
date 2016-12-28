import math
import os.path

import pandas as pd
import numpy as np

DATA_PATH = '/Users/irio/Desktop/serenata-data'
DISPLAY_KEYS = [
    'date',
    # 'document_id',
    'name',
    'net_value',
    # 'state',
    # 'party',
    # 'supplier',
    'price',
    'subquota',
    'day',
    'has_receipt',
    'is_in_office',
    'rosie_score',
    'score',
]


def full_path(path):
    return os.path.join(DATA_PATH, path)


def display(dataset):
    data = dataset.copy()
    data.rename(columns={'meal_price_outlier': 'price',
                         'over_monthly_subquota_limit': 'subquota',
                         'suspicious_traveled_speed_day': 'day',
                         'congressperson_name': 'name',
                         'issue_date': 'date',
                         'total_net_value': 'net_value'}, inplace=True)
    data['date'] = data['date'].str[:10]
    return data.head(13)[DISPLAY_KEYS]

def ranking():
    data = __irregularities()
    data = pd.merge(data, __is_in_office(data))
    data['has_receipt'] = data['year'] > 2011
    data['score'] = __score(data)
    data = data.sort_values(['is_in_office', 'has_receipt', 'score'],
                            ascending=[False, False, False])
    return data


def __is_in_office(data):
    return data \
        .groupby('applicant_id') \
        .apply(lambda x: x['year'].max() >= 2015) \
        .reset_index() \
        .rename(columns={0: 'is_in_office'})


def __score(data):
    data['rosie_score'] = __rosie_score(data)
    net_value_score = data['total_net_value'].apply(math.log) / \
        math.log(data['total_net_value'].max())
    return .5 * data['rosie_score'] + .5 * net_value_score


def __rosie_score(data):
    return .5 * data['meal_price_outlier_probability'] + \
        .3 * data['suspicious_traveled_speed_day_probability'] + \
        .2 * data['over_monthly_subquota_limit_probability']


def __irregularities():
    data = pd.read_csv(full_path('irregularities.xz'),
                       low_memory=False)
    is_valid_suspicion = data.select_dtypes(include=[np.bool]).any(axis=1)
    data = data[is_valid_suspicion]
    reimbursements = pd.read_csv(full_path('2016-12-06-reimbursements.xz'),
                                 low_memory=False)
    reimbursements = reimbursements.query('congressperson_id.notnull()')
    return pd.merge(data, reimbursements)
