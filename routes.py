from config import app, db, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from models import User, Recipe, CATEGORIES
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin
from werkzeug.utils import secure_filename
from uuid import uuid4



# Главная страница
@app.route("/")
def index():

    category = request.args.get('category')

    if category:
        recipes = db.session.scalars(
        db.select(Recipe).where(Recipe.status == "Опубликован", Recipe.category == category)
    ).all()
    else:
        recipes = db.session.scalars(
        db.select(Recipe).where(Recipe.status == "Опубликован")
    ).all()

    return render_template("home.html", recipes=recipes, categories=CATEGORIES)


# Страница просмотра отдельного рецепта
@app.route("/recipe/<int:recipe_id>")
def recipe_detail(recipe_id):
    recipe = db.get_or_404(Recipe, recipe_id)
    return render_template("recipe.html", recipe=recipe)


# Страница входа
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db.session.scalars(
            db.select(User).where(User.username == username)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))

        flash("Неверный логин или пароль.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


# Выход из аккаунта
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# Профиль
@app.route("/profile")
@login_required
def profile():
    user = db.session.get(User, current_user.id)

    recipes = db.session.scalars(
        db.select(Recipe).where(Recipe.user_id == user.id)
    ).all()

    return render_template(
        "profile.html",
        user=user,
        recipes=recipes
    )


# Страница регистрации
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Проверка: занят ли логин И почта
        existing_user = db.session.scalars(
            db.select(User).where(
                or_(User.username == username, User.email == email)
            )
        ).first()

        if existing_user:
            flash("Ошибка: это имя пользователя или почта уже заняты.", "error")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            email=email
        )

        new_user.set_password(password)

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
@login_required
def add_recipe():
    if request.method == "POST":

        title = request.form.get("title", "").strip()
        category = request.form.get("category")
        time = request.form.get("time", "").strip()
        portions = request.form.get("portions", "").strip()
        calories = request.form.get("calories", "").strip()
        ingredients = request.form.get("ingredients", "").splitlines()
        steps = request.form.get("steps", "").splitlines()

        # Получаем фотографию из формы
        image_file = request.files.get("image")

        # Проверяем заполнение текстовых полей
        if not all([title, time, portions, calories]) \
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
            image=f"uploads/{filename}",
            user_id=current_user.id,
            status="Опубликован"
        )

        try:
            db.session.add(new_recipe)
            db.session.commit()

        except Exception:
            db.session.rollback()
            image_path.unlink(missing_ok=True)
            raise

        return redirect(url_for("index"))

    return render_template("add_recipe.html", categories=CATEGORIES)