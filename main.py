import os
import random

from flask import Flask, render_template, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import Api, abort
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from data import db_session, user_resources, habit_resources, news_resources, comments_resources
from data.comments import Comments
from data.habits import Habits
from data.news import News
from data.users import User
from forms.CommentForm import ComForm
from forms.RegisterForm import RegisterForm
from forms.AddHabit import AddHabitForm
from forms.AddNews import AddNewsForm
from forms.Office import OfficeForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api = Api(app)
api.add_resource(user_resources.UsersResource, '/api/v1/users/<int:users_id>')
api.add_resource(user_resources.UsersListResource, '/api/v1/users')
api.add_resource(news_resources.NewsResource, '/api/v1/news/<int:news_id>')
api.add_resource(news_resources.NewsListResource, '/api/v1/news')
api.add_resource(habit_resources.HabitsResource, '/api/v1/habits/<int:habits_id>')
api.add_resource(habit_resources.HabitsListResource, '/api/v1/habits')
api.add_resource(comments_resources.CommentsResource, '/api/v1/comments/<int:comments_id>')
api.add_resource(comments_resources.CommentsListResource, '/api/v1/comments')
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
        path = ''
        news_index += 1
        creator_nickname = (db_sess.query(User).filter(User.id == news.user_id).first()).nickname
        for images in os.listdir('static/img/users_photo'):
            if images.split('.')[0] == creator_nickname:
                path = 'static/img/users_photo/' + images
        if path == '':
            path = 'static/img/users_photo/default.jpg'
        comments = []
        if news.comms:
            if ';' in news.comms:
                for com_id in news.comms.split(';'):
                    comments.append(db_sess.query(Comments).filter(Comments.id == com_id).first())
            elif len(news.comms) == 1:
                com_id = news.comms
                comments = [db_sess.query(Comments).filter(Comments.id == com_id).first()]
        else:
            comments = []
        if len(comments) > 1:
            comments = sorted(comments, key=lambda x: x.created_date)
        comments_main = []
        for com in comments:
            comentor_nickname = db_sess.query(User).filter(User.id == com.user_id).first().nickname
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
                         'creator': creator_nickname,
                         'path': path})
        if news_index == 3:
            break
    return render_template("index.html", top_habits=top_habits, top_news=top_news, random_id=random.randint(1, 2 ** 16))


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


@app.route('/info', methods=['GET', 'POST'])
def about_page():
    return render_template('about.html')


@app.route("/add_habit", methods=['GET', 'POST'])
def add_habit():
    form = AddHabitForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        habit = Habits()
        habit.creator = current_user.id
        habit.count = 0
        habit.reposts = 0
        habit.type = form.habit_name.data
        habit.period = form.duration.data
        habit.about_link = form.about_habit.data
        db_sess.add(habit)
        db_sess.commit()
        return redirect('/')
    return render_template("add_habit.html", form=form)


@app.route("/add_habit/<int:habit_id>", methods=['GET', 'POST'])
def repost_habit(habit_id):
    habit_id = habit_id
    db_sess = db_session.create_session()
    to_new = db_sess.query(User).filter(User.id == current_user.id).first()
    if to_new.habit and str(habit_id) not in str(to_new.habit):
        to_new.habit = str(to_new.habit) + ';' + str(habit_id)
    else:
        to_new.habit = str(habit_id)
    db_sess.add(to_new)

    to_new2 = db_sess.query(Habits).filter(Habits.id == habit_id).first()
    to_new2.reposts = str(int(to_new2.reposts) + 1)
    db_sess.add(to_new2)
    db_sess.commit()
    return redirect('/')


@app.route("/com_add/<int:new_id>", methods=['GET', 'POST'])
def comm_add(new_id):
    form = ComForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        to_new = db_sess.query(News).filter(News.id == new_id).first()
        idd = len(db_sess.query(Comments).all()) + 1
        to_new.comms = str(to_new.comms) + ';{}'.format(idd)
        com = Comments()
        com.user_id = current_user.id
        com.content = form.content.data
        db_sess.add(com)
        db_sess.add(to_new)
        db_sess.commit()
        return redirect('/')
    return render_template("add_com.html", form=form)


@app.route("/office", methods=['GET', 'POST'])
@login_required
def my_office():
    form = OfficeForm()
    path = ''
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if user:
            form.name.data = user.name
            form.surname.data = user.surname
            form.nickname.data = user.nickname
            form.age.data = user.age
            form.status.data = user.status
            form.email.data = user.email
            form.hashed_password.data = user.hashed_password
            form.city_from.data = user.city_from
        else:
            abort(404)
    if form.validate_on_submit():
        if '.jpg' in request.files['file']:
            input_file = request.files['file']
            new_img = open("static/img/users_photo/" + str(current_user.nickname) + ".jpg", 'wb')
            new_img.write(input_file.read())
            new_img.close()
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if user:
            user.name = form.name.data
            user.surname = form.surname.data
            user.nickname = form.nickname.data
            user.age = form.age.data
            user.status = form.status.data
            user.email = form.email.data
            user.hashed_password = form.hashed_password.data
            user.city_from = form.city_from.data
            db_sess.merge(current_user)
            db_sess.commit()
            return redirect('/office')
        else:
            abort(404)
    for images in os.listdir('static/img/users_photo'):
        if images.split('.')[0] == current_user.nickname:
            path = 'static/img/users_photo/' + images
    if path == '':
        path = 'static/img/users_photo/default.jpg'
    return render_template('office.html',
                           form=form, path=path, random_id=random.randint(1, 2 ** 16))


@app.route("/add_news", methods=['GET', 'POST'])
def add_news():
    form = AddNewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.user_id = current_user.id
        news.title = form.news_name.data
        news.content = form.news_content.data
        db_sess.add(news)
        db_sess.commit()
        return redirect('/')
    return render_template("add_news.html", form=form)


@app.route("/news", methods=['GET', 'POST'])
def news():
    db_sess = db_session.create_session()
    rec_news = db_sess.query(News).all()
    top_news = []
    news_index = 0
    path = 'static/img/users_photo/default.jpg'
    for news in rec_news:
        path = ''
        news_index += 1
        creator_nickname = (db_sess.query(User).filter(User.id == news.user_id).first()).nickname
        for images in os.listdir('static/img/users_photo'):
            if images.split('.')[0] == creator_nickname:
                path = 'static/img/users_photo/' + images
        if path == '':
            path = 'static/img/users_photo/default.jpg'
        comments = []
        if news.comms:
            if ';' in news.comms:
                for com_id in news.comms.split(';'):
                    comments.append(db_sess.query(Comments).filter(Comments.id == com_id).first())
            elif len(news.comms) == 1:
                com_id = news.comms
                comments = [db_sess.query(Comments).filter(Comments.id == com_id).first()]
        else:
            comments = []
        if len(comments) > 1:
            comments = sorted(comments, key=lambda x: x.created_date)
        comments_main = []
        for com in comments:
            comentor_nickname = db_sess.query(User).filter(User.id == com.user_id).first().nickname
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
                         'creator': creator_nickname,
                         'path': path})
    return render_template("news.html", top_news=top_news, path=path, random_id=random.randint(1, 2 ** 16))


if __name__ == '__main__':
    # app.run()
    # port = int(os.environ.get("PORT", 5000))
    app.run(host='127.0.0.1', port=2000)
