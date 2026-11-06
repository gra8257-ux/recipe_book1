from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

# Базы
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "super-secret-key"  # Секретный ключ для подписи куки (сессий) и сообщений flash().
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)


# работа с пользователями
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"  # помощь в отслеживании юзеров с помощью консоли


# Главная страница.
@app.route("/")
def index():
    return render_template("home.html")


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
    recipe = RECIPES.get(recipe_id)

    # Если рецепта с таким номером нет, показываем ошибку 404
    if recipe is None:
        return "Рецепт не найден", 404

    return render_template("recipe.html", recipe=recipe)


# Отдельная страница регистрации.
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
            flash(f"Ошибка: Логин '{username}' уже занят. Придумайте другой.", "error")
            return redirect(url_for("register"))

        existing_email = db.session.scalars(
            db.select(User).where(User.email == email)
        ).first()

        if existing_email:
            flash(f"Ошибка: Почта '{email}' уже используется. Введите другую.", "error")
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

    # Список пользователей.
    all_users = db.session.scalars(db.select(User)).all()
    return render_template("register.html", users=all_users)


# Удаление аккаунта ( позже сдлеать только для админа )
@app.route("/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    # Ищем пользователя по ID. Если нет — вернет ошибку 404
    user = db.get_or_404(User, user_id)

    # Удаляем объект и сохраняем изменения в базу
    db.session.delete(user)
    db.session.commit()

    flash(f"Пользователь '{user.username}' успешно удален.", "success")
    return redirect(url_for("register"))


# Запуск
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("База данных и таблицы готовы.")

    app.run(debug=True)
