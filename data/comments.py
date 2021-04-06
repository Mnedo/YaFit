import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Comments(SqlAlchemyBase):
    __tablename__ = 'comments'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    content = sqlalchemy.Column(sqlalchemy.String)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    news_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("news.id"))
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    news = orm.relation('News')

    # categories = orm.relation("Category", secondary="association", backref="news")
