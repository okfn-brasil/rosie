from collections import OrderedDict
from itertools import chain
import json
import os

from decouple import config
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient

#from dataset import DISPLAY_KEYS, full_path, ranking
# ranking().to_csv(full_path('ranking.csv'), index=False)
app = Flask(__name__)
mongodb = MongoClient(config('MONGODB_URI', default=os.environ['MONGODB_URI']), document_class=OrderedDict)
db = getattr(mongodb, config('MONGODB_DATABASE', default=os.environ['MONGODB_DATABASE']))

DISPLAY_KEYS = OrderedDict([
    ('url', 'URL'),
    ('issue_date', 'Data do gasto'),
    ('congressperson_name', 'Deputado'),
    ('total_net_value', 'Valor'),
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


@app.route('/', methods=['GET'])
def root():
    reported_docs = db.reports.find({}, {'_id': 0, 'documents':1})
    reported_docs = chain(*[doc['documents'] for doc in reported_docs])
    query = {
        'document_id': {'$nin': list(reported_docs)},
        'status': {'$ne': 'false_positive'},
    }
    ranking_docs = db.ranking.find(query, {'_id': 0}) \
        .sort([('is_in_office', -1), ('has_receipt', -1), ('score', -1)]) \
        .limit(20)
    columns = DISPLAY_KEYS.copy()
    for key in ['year', 'document_id', 'applicant_id', 'rosie_score', 'score']:
        columns.pop(key, None)

    return render_template('index.html',
                           ranking=ranking_docs,
                           columns=columns)

@app.route('/ranking', methods=['POST'])
def update_ranking():
    query = {'document_id': int(request.form['document_id'])}
    status = request.form['status']
    if status in ['false_positive', 'under_investigation']:
        db.ranking.update_one(query, {
            '$set': {'status': status}
        })
    elif status == 'none':
        db.ranking.update_one(query, {
            '$unset': {'status': True}
        })
    return '', 200, {}

@app.route('/reports', methods=['GET'])
def get_reports():
    return jsonify([clean(document) for document in db.reports.find()])


@app.route('/reports', methods=['POST'])
def post_reports():
    data = clean(request.form)
    if not all(data.get(key) for key in ('documents', 'email')):
        error = {'error': 'Missing `documents` and `email` data.'}
        return jsonify(error), 400

    filter_ = {'documents': data['documents'], 'email': data['email']}
    db.reports.update_one(filter_, {'$set': data}, upsert=True)
    return jsonify(clean(db.reports.find(filter_)[0]))


def clean(document):
    whitelist = (
        'documents',
        'email',
        'illegal',
        'refund',
        'report_id',
        'under_investigation'
    )
    cleaned = {key: val for key, val in document.items() if key in whitelist}

    if isinstance(cleaned.get('documents'), str):
        ids = cleaned['documents'].split(',')
        cleaned['documents'] = list(filter(bool, map(to_int, ids)))

    if isinstance(cleaned.get('refund'), str):
        try:
            cleaned['refund'] = float(cleaned['refund'])
        except ValueError:
            cleaned['refund'] = None

    for key in ('illegal', 'under_investigation'):
        if isinstance(cleaned.get(key), str):
            cleaned[key] = cleaned[key].lower() in ('true', '1')

    return cleaned


def to_int(value):
    try:
        return int(value)
    except ValueError:
        return None


if __name__ == '__main__':
    app.run()
