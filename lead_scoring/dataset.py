import math
import os.path
from argparse import ArgumentParser
from collections import OrderedDict

import numpy as np
import pandas as pd

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


def suspicions_list():
    data = _suspicions()
    data['has_receipt'] = data['year'] > 2011
    data = data.sort_values(['year', 'has_receipt'],
                            ascending=[False, False])
    return display(data)


def _suspicions():
    data = pd.read_csv('suspicions.xz', low_memory=False)
    is_valid_suspicion = data.select_dtypes(include=[np.bool]).any(axis=1)
    data = data[is_valid_suspicion]
    reimbursements = pd.read_csv('reimbursements.xz', low_memory=False)
    reimbursements = reimbursements.query('congressperson_id.notnull()')
    return pd.merge(data, reimbursements)


def main():
    dataset = suspicions_list()
    dataset.to_csv('maratonny.csv', index=False)


if __name__ == '__main__':
    description = """
    Script to generate Maratonny's list of suspicions to be investigated
    """
    parser = ArgumentParser(description=description)
    parser.add_argument(
        '--data-path', '-c', default='',
        help=('Path to a directory where you can find:\n'
              '  - reimbursements.xz\n  - suspicions.xz')
    )
    args = parser.parse_args()
    main()
