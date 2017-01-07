from collections import OrderedDict
import math
import os.path

import pandas as pd
import numpy as np

DATA_PATH = '/Users/irio/Desktop/serenata-data'
DISPLAY_KEYS = OrderedDict([
    ('issue_date', 'Data do gasto'),
    ('congressperson_name', 'Deputado'),
    ('total_net_value', 'Valor'),
    ('url', 'URL'),
    ('meal_price_outlier', 'Preço de refeição suspeito?'),
    ('over_monthly_subquota_limit', 'Acima da subcota?'),
    ('suspicious_traveled_speed_day', 'Distância viajada suspeita?'),
    ('has_receipt', 'Tem recibo?'),
    ('is_in_office', 'Em mandato?'),
    ('rosie_score', 'Nível de suspeita'),
    ('score', 'Ranking'),
    ('year', 'Ano'),
    ('document_id', 'ID'),
    ('applicant_id', 'ID Deputado'),
])


def full_path(path):
    return os.path.join(DATA_PATH, path)


def display(dataset):
    data = dataset.copy()
    data['issue_date'] = data['issue_date'].str[:10]
    data['url'] = data['document_id'] \
        .apply(lambda x: 'https://jarbas.datasciencebr.com/#/documentId/{}'.format(x))
    # data['rosie_score'] = data['rosie_score'].apply(__display_percentage)
    # data['score'] = data['score'].apply(__display_percentage)
    # data['total_net_value'] = data['total_net_value'] \
    #     .apply(lambda x: 'R$ {0:.2f}'.format(x))
    data = data[[k for k in DISPLAY_KEYS.keys()]]
    # data.rename(columns=DISPLAY_KEYS, inplace=True)
    return data

def __display_percentage(values):
    return '{0:.2f}%'.format(values * 100)

def ranking():
    data = __irregularities()
    # import ipdb; ipdb.set_trace()
    data = pd.merge(data, __is_in_office(data))
    data['has_receipt'] = data['year'] > 2011
    data['score'] = __score(data)
    data = data.sort_values(['is_in_office', 'has_receipt', 'score'],
                            ascending=[False, False, False])
    remove_receipts_from_same_case(data)
    return display(data)

def remove_receipts_from_same_case(data):
    speed_day_keys = ['applicant_id',
                      'issue_date',
                      'suspicious_traveled_speed_day']
    subquota_keys = ['applicant_id',
                     'month',
                     'over_monthly_subquota_limit']
    data.drop_duplicates(speed_day_keys, inplace=True)
    data.drop_duplicates(subquota_keys, inplace=True)
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
