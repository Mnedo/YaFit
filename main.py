import os
from flask import Flask
from data import db_session


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

db_session.global_init("db/habits.db")
db_sess = db_session.create_session()




if __name__ == '__main__':
    app.run()
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port)
