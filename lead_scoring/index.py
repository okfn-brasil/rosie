from collections import OrderedDict
from itertools import chain
import json
import os

from decouple import config
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient

from dataset import DISPLAY_KEYS, full_path, ranking

# ranking().to_csv(full_path('ranking.csv'), index=False)
app = Flask(__name__)
mongodb = MongoClient(config('MONGODB_URI', default=os.environ['MONGODB_URI']), document_class=OrderedDict)
db = getattr(mongodb, config('MONGODB_DATABASE', default=os.environ['MONGODB_DATABASE']))


@app.route('/', methods=['GET'])
def root():
    reported_docs = db.reports.find({}, {'_id': 0, 'documents':1})
    reported_docs = chain(*[doc['documents'] for doc in reported_docs])
    query = {'document_id': {'$nin': list(reported_docs)}}
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
    if request.form['under_investigation'] == '1':
        db.ranking.update_one(query, {
            '$set': {'under_investigation': True}
        })
    elif request.form['under_investigation'] == '0':
        db.ranking.update_one(query, {
            '$unset': {'under_investigation': True}
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
