import os
from flask import Flask, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import Api
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


# @app.route("/add_habit/<int:habit_id>", methods=['GET', 'POST'])
# def repost_habit(habit_id):
#     habit_id = habit_id
#     db_sess = db_session.create_session()
#     to_new = db_sess.query(User).filter(User.id == current_user.id).first()
#     to_new.habit = to_new.habit + ';' + str(habit_id)
#     db_sess.add(to_new)
#
#     to_new = db_sess.query(Habits).filter(Habits.id == habit_id).first()
#     to_new.reposts = str(int(to_new.reposts) + 1)
#     db_sess.add(to_new)
#
#     db_sess.commit()


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
def my_office():
    return render_template('office.html')


@app.route("/add_news", methods=['GET', 'POST'])
def add_news():
    form = AddNewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.user_id = current_user.id
        news.title = form.news_name
        news.content = form.news_content
        db_sess.add(news)
        db_sess.commit()
        return redirect('/')
    return render_template("add_news.html", form=form)



if __name__ == '__main__':
    app.run()
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host='0.0.0.0', port=port)
