from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from config import app, db, login_manager


CATEGORIES = ["горячее", "холодное", "супы", "закуски", "выпечка и десерты", "напитки", "соусы"]

# Работа с пользователями
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# Работа с рецептами
class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)

    # Путь к фотографии рецепта
    image = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(100), nullable=False)
    portions = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.JSON, nullable=False)
    steps = db.Column(db.JSON, nullable=False)

    # ID пользователя
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Статус рецепта
    status = db.Column(db.String(30), default="Опубликован", nullable=False)

# Создание базы данных и таблиц
# Выполняется и при запуске через Gunicorn на Render
with app.app_context():

    db.create_all()

    # Проверяем, есть ли столбцы в старой таблице recipes
    columns = db.inspect(db.engine).get_columns("recipes")
    column_names = [column["name"] for column in columns]

    # Если столбца image нет, добавляем его
    if "image" not in column_names:
        db.session.execute(
            db.text(
                "ALTER TABLE recipes ADD COLUMN image VARCHAR(255)"
            )
        )

    # Если столбца status нет, добавляем его
    if "status" not in column_names:
        db.session.execute(
            db.text(
                "ALTER TABLE recipes ADD COLUMN status VARCHAR(30) DEFAULT 'Опубликован'"
            )
        )

    db.session.commit()

    print("База данных и таблицы готовы.")

# Загрузчик Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))