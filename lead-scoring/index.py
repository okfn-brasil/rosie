from flask import Flask

from dataset import full_path, ranking

ranking().to_csv(full_path('ranking.csv'))
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
