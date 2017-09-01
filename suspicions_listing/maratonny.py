from os.path import join
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
    jarbas_url = 'https://jarbas.datasciencebr.com/#/documentId/{}'
    data['url'] = data['document_id'] \
        .apply(lambda x: jarbas_url.format(x))
    data = data[[k for k in DISPLAY_KEYS.keys()]]
    return data


def _display_percentage(values):
    return '{0:.2f}%'.format(values * 100)


def suspicions_list(data_path):
    data = _suspicions(data_path)
    data['has_receipt'] = data['year'] > 2011
    data = data.sort_values(['year', 'has_receipt'],
                            ascending=[False, False])
    return display(data)


def _suspicions(data_path):
    data = pd.read_csv(join(data_path, 'suspicions.xz'), low_memory=False)
    is_valid_suspicion = data.select_dtypes(include=[np.bool]).any(axis=1)
    data = data[is_valid_suspicion]
    reimbursements = pd.read_csv(join(data_path, 'reimbursements.xz'),
                                 low_memory=False)
    reimbursements = reimbursements.query('congressperson_id.notnull()')
    return pd.merge(data, reimbursements)


def remove_hackatonny(data):
    reports = pd.read_csv('reports.csv')
    reports = reports.apply(lambda row: _documents_id(row['documents']), axis=1)
    data = data.drop(axis='rows', labels=list(_dropable_rows(reports, data)))
    return data


def _dropable_rows(reports, dataset):
    doc_list = []
    for _ in reports:
        for i in _:
            doc_list.append(int(i))

    data = dataset.copy()
    data = data[data['document_id'].isin(doc_list)]
    return list(data.index)


def _documents_id(doc_list):
    doc_list = doc_list.split(sep=',')
    for i in range(len(doc_list)):
        if not doc_list[i].isalnum():
            doc_list[i] = ''.join([j for j in doc_list[i] if j.isalnum()])

    return doc_list


def main(data_path):
    dataset = suspicions_list(data_path)
    dataset = remove_hackatonny(dataset)
    dataset.to_csv(join(data_path, 'maratonny.csv'), index=False)


if __name__ == '__main__':
    description = """
    Script to generate Maratonny's list of suspicions to be investigated
    """
    parser = ArgumentParser(description=description)
    parser.add_argument(
        '--data-path', '-c', default='',
        help=('Path to a directory where you can find:'
              '  reimbursements.xz, suspicions.xz and rankings.csv')
    )
    args = parser.parse_args()
    main(args.data_path)
