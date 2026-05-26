from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key"

# MongoDB Atlas
client = MongoClient(os.getenv("MONGO_URI"))
db = client["flaskdb"]
users_collection = db["users"]

# Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Clase Usuario
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"_id": ObjectId(user_id)})
    
    if user_data:
        return User(user_data)
    
    return None

# Home
@app.route("/")
def home():
    return redirect(url_for("login"))

# Registro
@app.route("/register", methods=["GET", "POST"])
def register():
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = users_collection.find_one({"username": username})

        if existing_user:
            flash("El usuario ya existe", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        users_collection.insert_one({
            "username": username,
            "password": hashed_password
        })

        flash("Usuario registrado correctamente", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user_data = users_collection.find_one({"username": username})

        if user_data and check_password_hash(user_data["password"], password):

            user = User(user_data)
            login_user(user)

            flash("Bienvenido", "success")
            return redirect(url_for("dashboard"))

        flash("Credenciales incorrectas", "danger")

    return render_template("login.html")

# Dashboard protegido
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.username)

# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "warning")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)