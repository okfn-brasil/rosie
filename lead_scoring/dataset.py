from collections import OrderedDict
import math
import os.path

import pandas as pd
import numpy as np

DISPLAY_KEYS = OrderedDict([
    ('url', 'URL'),
    ('issue_date', 'Data do gasto'),
    ('congressperson_name', 'Deputado'),
    ('total_net_value', 'Valor'),
    ('meal_price_outlier', 'Preço de refeição suspeito?'),
    ('over_monthly_subquota_limit', 'Acima da subcota?'),
    ('suspicious_traveled_speed_day', 'Distância viajada suspeita?'),
    ('invalid_cnpj_cpf', 'CNPJ ou CPF inválido?'),
    ('election_expenses', 'É gasto de eleição?'),
    ('irregular_companies_classifier', 'Empresa irregular?'),
    ('has_receipt', 'Tem recibo?'),
    ('is_in_office', 'Em mandato?'),
    ('year', 'Ano'),
    ('document_id', 'ID'),
    ('applicant_id', 'ID Deputado'),
])


def display(dataset):
    data = dataset.copy()
    data['issue_date'] = data['issue_date'].str[:10]
    data['url'] = data['document_id'] \
        .apply(lambda x: 'https://jarbas.datasciencebr.com/#/documentId/{}'.format(x))
    data = data[[k for k in DISPLAY_KEYS.keys()]]
    return data

def _display_percentage(values):
    return '{0:.2f}%'.format(values * 100)

def ranking():
    data = _irregularities()
    data = pd.merge(data, _is_in_office(data))
    data['has_receipt'] = data['year'] > 2011
    data = data.sort_values(['is_in_office', 'has_receipt'],
                            ascending=[False, False])
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

def _is_in_office(data):
    return data \
        .groupby('applicant_id') \
        .apply(lambda x: x['year'].max() >= 2016) \
        .reset_index() \
        .rename(columns={0: 'is_in_office'})


def _irregularities():
    data = pd.read_csv('suspicions.xz', low_memory=False)
    is_valid_suspicion = data.select_dtypes(include=[np.bool]).any(axis=1)
    data = data[is_valid_suspicion]
    reimbursements = pd.read_csv('reimbursements.xz', low_memory=False)
    reimbursements = reimbursements.query('congressperson_id.notnull()')
    return pd.merge(data, reimbursements)
