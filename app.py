
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError


# Папки и база данных

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "database.db"


# Создание приложения

app = Flask(__name__)

app.config["SECRET_KEY"] = "super-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_ECHO"] = True

# Максимальный размер загружаемой фотографии — 5 МБ
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

db = SQLAlchemy(app)


# Папка для фотографий рецептов

UPLOAD_FOLDER = Path(app.static_folder) / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Разрешённые форматы изображений
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


# Работа с пользователями

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

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


# Главная страница

@app.route("/")
def index():
    recipes = db.session.scalars(db.select(Recipe)).all()
    return render_template("home.html", recipes=recipes)


# Временные рецепты для проверки страницы просмотра

RECIPES = {
    1: {
        "title": "Паста с томатным соусом",
        "description": "Простая и вкусная паста с ароматным томатным соусом.",
        "time": "30 минут",
        "portions": "2 порции",
        "ingredients": [
            "200 г макарон",
            "3 помидора",
            "2 зубчика чеснока",
            "2 столовые ложки оливкового масла",
            "Соль и специи по вкусу"
        ],
        "steps": [
            "Отварите макароны в подсоленной воде до готовности.",
            "Нарежьте помидоры небольшими кусочками.",
            "Измельчите чеснок и обжарьте его на оливковом масле.",
            "Добавьте помидоры и тушите около 10 минут.",
            "Смешайте соус с макаронами и подавайте к столу."
        ]
    },

    2: {
        "title": "Домашний овощной суп",
        "description": "Лёгкий овощной суп для вкусного домашнего обеда.",
        "time": "40 минут",
        "portions": "4 порции",
        "ingredients": [
            "3 картофелины",
            "1 морковь",
            "1 луковица",
            "1,5 литра воды",
            "Соль и зелень по вкусу"
        ],
        "steps": [
            "Очистите и нарежьте картофель.",
            "Нарежьте лук и натрите морковь.",
            "Вскипятите воду и добавьте картофель.",
            "Добавьте лук и морковь.",
            "Варите до готовности овощей, затем добавьте зелень."
        ]
    },

    3: {
        "title": "Шоколадный десерт",
        "description": "Нежный шоколадный десерт для любителей сладкого.",
        "time": "25 минут",
        "portions": "3 порции",
        "ingredients": [
            "100 г тёмного шоколада",
            "100 мл сливок",
            "2 столовые ложки сахара",
            "1 яйцо"
        ],
        "steps": [
            "Растопите шоколад на водяной бане.",
            "Добавьте сливки и перемешайте.",
            "Отдельно взбейте яйцо с сахаром.",
            "Соедините обе смеси.",
            "Разложите десерт по формочкам и охладите."
        ]
    }
}


# Страница просмотра отдельного рецепта

@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = db.get_or_404(Recipe, recipe_id)
    return render_template("recipe.html", recipe=recipe)


# Страница регистрации

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        existing_username = db.session.scalars(
            db.select(User).where(User.username == username)
        ).first()

        if existing_username:
            flash(
                f"Ошибка: Логин '{username}' уже занят. Придумайте другой.",
                "error"
            )
            return redirect(url_for("register"))

        existing_email = db.session.scalars(
            db.select(User).where(User.email == email)
        ).first()

        if existing_email:
            flash(
                f"Ошибка: Почта '{email}' уже используется. Введите другую.",
                "error"
            )
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            flash("Пользователь успешно создан!", "success")

        except IntegrityError:
            db.session.rollback()
            flash("Ошибка при сохранении. Попробуйте еще раз.", "error")

        return redirect(url_for("register"))

    # Список пользователей
    all_users = db.session.scalars(db.select(User)).all()

    return render_template("register.html", users=all_users)


# Удаление аккаунта (позже сделать только для администратора)

@app.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = db.get_or_404(User, user_id)

    db.session.delete(user)
    db.session.commit()

    flash(f"Пользователь '{user.username}' успешно удален.", "success")

    return redirect(url_for("register"))


# Добавление рецептов с фотографиями

@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":

        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        time = request.form.get("time", "").strip()
        portions = request.form.get("portions", "").strip()
        calories = request.form.get("calories", "").strip()

        ingredients = request.form.get("ingredients", "").splitlines()
        steps = request.form.get("steps", "").splitlines()

        # Получаем фотографию из формы
        image_file = request.files.get("image")

        # Проверяем заполнение текстовых полей
        if not all([title, category, time, portions, calories]) \
                or not ingredients or not steps:
            return "Заполните все поля", 400

        # Проверяем, выбрана ли фотография
        if not image_file or image_file.filename == "":
            return "Выберите фотографию рецепта", 400

        # Проверяем формат фотографии
        if "." not in image_file.filename:
            return "Неверный формат файла", 400

        extension = image_file.filename.rsplit(".", 1)[-1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            return "Разрешены только JPG, JPEG, PNG и WEBP", 400

        # Создаём уникальное имя файла
        filename = secure_filename(f"{uuid4().hex}.{extension}")

        # Сохраняем фотографию в папку uploads
        image_path = UPLOAD_FOLDER / filename
        image_file.save(image_path)

        # Создаём новый рецепт
        new_recipe = Recipe(
            title=title,
            category=category,
            time=time,
            portions=portions,
            calories=calories,
            ingredients=ingredients,
            steps=steps,
            image=f"uploads/{filename}"
        )

        try:
            db.session.add(new_recipe)
            db.session.commit()

        except Exception:
            db.session.rollback()
            image_path.unlink(missing_ok=True)
            raise

        return redirect(url_for("index"))

    return render_template("add_recipe.html")


# Запуск приложения

if __name__ == "__main__":
    with app.app_context():

        db.create_all()

        # Проверяем, есть ли столбец image в старой таблице recipes
        columns = db.inspect(db.engine).get_columns("recipes")
        column_names = [column["name"] for column in columns]

        # Если столбца нет, добавляем его
        if "image" not in column_names:
            db.session.execute(
                db.text(
                    "ALTER TABLE recipes ADD COLUMN image VARCHAR(255)"
                )
            )
            db.session.commit()

        print("База данных и таблицы готовы.")

    app.run(debug=True)
