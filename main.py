import os
from flask import Flask, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
import wikipedia
from data import db_session
from data.comments import Comments
from data.habits import Habits
from data.news import News
from data.users import User
from forms.RegisterForm import RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db_session.global_init("db/habits.db")
db_sess = db_session.create_session()
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    db_sess = db_session.create_session()
    habits = db_sess.query(Habits).all()
    habits = sorted(habits, key=lambda x: -int(x.reposts))
    top_habits = []
    habit_index = 0
    for habit in habits:
        habit_index += 1
        creator_nickname = (db_sess.query(User).filter(User.id == habit.creator).first()).nickname
        top_habits.append({'id': habit.id,
                           'type': habit.type,
                           'period': habit.period,
                           'about_link': habit.about_link,
                           'count': habit.count,
                           'reposts': habit.reposts,
                           'creator': creator_nickname})
        if habit_index == 3:
            break
    rec_news = db_sess.query(News).all()
    rec_news = sorted(rec_news, key=lambda x: x.created_date)
    top_news = []
    news_index = 0
    for news in rec_news:
        news_index += 1
        creator_nickname = (db_sess.query(User).filter(User.id == habit.creator).first()).nickname
        comments = []
        if news.comms:
            if ';' in news.comms:
                for com_id in news.comms.split(';'):
                    comments.append(db_sess.query(Comments).filter(Comments.id == com_id).first())
            elif len(news.comms) == 1:
                comments = [db_sess.query(Comments).filter(Comments.id == com_id).first()]
        else:
            comments = []
        if len(comments) > 1:
            comments = sorted(comments, key=lambda x: x.created_date)
        comments_main = []
        for com in comments:
            comentor_nickname = db_sess.query(User).filter(User.id == habit.creator).first().nickname
            comments_main.append({'id': com.id,
                         'content': com.content,
                         'created_date': com.created_date.strftime("%A %d %B %Y"),
                         'creator': comentor_nickname})
        comments = comments_main
        top_news.append({'id': news.id,
                         'title': news.title,
                         'content': news.content,
                         'created_date': news.created_date.strftime("%A %d %B %Y"),
                         'comms': comments,
                         'creator': creator_nickname})
        if news_index == 5:
            break
    return render_template("index.html", top_habits=top_habits, top_news=top_news)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            nickname=form.nickname.data,
            name=form.nickname.data,
            email=form.email.data,
            about=form.about.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


if __name__ == '__main__':
    app.run()
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port)
