import json
import os

from decouple import config
from flask import Flask, jsonify, request
from pymongo import MongoClient

# from dataset import full_path, ranking

# ranking().to_csv(full_path('ranking.csv'), index=False)
app = Flask(__name__)
mongodb = MongoClient(config('MONGODB_URI', default=os.environ['MONGODB_URI']))
db = getattr(mongodb, config('MONGODB_DATABASE', default=os.environ['MONGODB_DATABASE']))


@app.route('/', methods=['GET'])
def get():
    return jsonify([clean(document) for document in db.reports.find()])


@app.route('/', methods=['POST'])
def post():
    data = clean(request.get_json())
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
