from flask_restful import reqparse, abort, Api, Resource
from flask import Flask, jsonify
import sqlite3
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class DB:
    def __init__(self):
        conn = sqlite3.connect("sqlite/databases/mydb1.db", check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (user_name, password_hash) 
                          VALUES (?,?)''', (user_name, password_hash))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def delete(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM users WHERE id = ?''', (str(user_id),))
        cursor.close()
        self.connection.commit()

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)


class NewsModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             user_id INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, content, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO news 
                          (title, content, user_id) 
                          VALUES (?,?,?)''', (title, content, str(user_id)))
        cursor.close()
        self.connection.commit()

    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (str(news_id),))
        row = cursor.fetchone()
        return row

    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = ?",
                           (str(user_id),))
        else:
            cursor.execute("SELECT * FROM news")
        rows = cursor.fetchall()
        return rows

    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE id = ?''', (str(news_id),))
        cursor.close()
        self.connection.commit()

    def change(self, news_id, type1, new_text):
        cursor = self.connection.cursor()
        if type1 == 'title':
            cursor.execute('''UPDATE news SET title="{}" WHERE id={}'''.format(new_text, news_id))
        else:
            cursor.execute('''UPDATE news SET content="{}" WHERE id={}'''.format(new_text, news_id))
        cursor.close()
        self.connection.commit()


def abort_if_news_not_found(news_id):
    if not NewsModel(db.get_connection()).get(news_id):
        abort(404, message="News {} not found".format(news_id))


def abort_if_user_not_found(user_id):
    if not UsersModel(db.get_connection()).get(user_id):
        abort(404, message="User {} not found".format(user_id))


class News(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        news = NewsModel(db.get_connection()).get(news_id)
        return jsonify({'news': news})

    def delete(self, news_id):
        abort_if_news_not_found(news_id)
        NewsModel(db.get_connection()).delete(news_id)
        return jsonify({'success': 'OK'})


class User(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        user = UsersModel(db.get_connection()).get(user_id)
        return jsonify({'user': user})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        UsersModel(db.get_connection()).delete(user_id)
        return jsonify({'success': 'OK'})


parser = reqparse.RequestParser()

parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('user_id', required=True, type=int)

parser1 = reqparse.RequestParser()
parser1.add_argument('user_name', required=True)
parser1.add_argument('password_hash', required=True)


class UsersList(Resource):
    def get(self):
        users = UsersModel(db.get_connection()).get_all()
        return jsonify({'users': users})

    def post(self):
        args = parser1.parse_args()
        users = UsersModel(db.get_connection())
        users.insert(args['user_name'], args['password_hash'])
        return jsonify({'success': 'OK'})


class NewsList(Resource):
    def get(self):
        news = NewsModel(db.get_connection()).get_all()
        return jsonify({'news': news})

    def post(self):
        args = parser.parse_args()
        news = NewsModel(db.get_connection())
        news.insert(args['title'], args['content'], args['user_id'])
        return jsonify({'success': 'OK'})


db = DB()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api = Api(app)

api.add_resource(NewsList, '/news', '/')  # для списка объектов, но со "/"
api.add_resource(News, '/news/<int:news_id>')  # для одного объекта

api.add_resource(UsersList, '/users')  # для списка объектов
api.add_resource(User, '/users/<int:user_id>')  # для одного объекта

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
