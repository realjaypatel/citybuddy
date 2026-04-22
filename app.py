from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import base64

app = Flask(__name__)
app.secret_key = "secret123"

# -------------------------
# MONGODB
# -------------------------
MONGO_URI = "mongodb+srv://user:user@cluster0.u3fdtma.mongodb.net/citybuddy?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["hf"]

posts_col = db["posts"]
users_col = db["users"]

# -------------------------
# INIT ADMIN
# -------------------------
def create_admin():
    if users_col.count_documents({"username": "admin"}) == 0:
        users_col.insert_one({
            "username": "admin",
            "password": generate_password_hash("admin123")
        })

# -------------------------
# HOME (PUBLIC EXPLORE)
# -------------------------
@app.route("/")
def home():
    posts = list(posts_col.find())

    city = request.args.get("city", "").lower()
    role = request.args.get("role", "")

    if city:
        posts = [p for p in posts if city in p.get("city", "").lower()]

    if role:
        posts = [p for p in posts if p.get("role") == role]

    posts = posts[::-1]

    return render_template("index.html", posts=posts)

# -------------------------
# SIGNUP
# -------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if users_col.find_one({"username": username}):
            return "User already exists!"

        users_col.insert_one({
            "username": username,
            "password": generate_password_hash(password)
        })

        return redirect("/login")

    return render_template("signup.html")

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_col.find_one({"username": username})

        if user and check_password_hash(user["password"], password):
            session["auth"] = True
            session["user"] = username
            return redirect("/admin")

        return "Invalid credentials"

    return render_template("login.html")

# -------------------------
# ADMIN PANEL
# -------------------------
@app.route("/admin")
def admin():
    if not session.get("auth"):
        return redirect("/login")

    posts = list(posts_col.find())
    return render_template("admin.html", posts=posts)

# -------------------------
# CREATE
# -------------------------
@app.route("/create", methods=["GET", "POST"])
def create():
    if not session.get("auth"):
        return redirect("/login")

    if request.method == "POST":
        image_file = request.files.get("image")

        image_data = None
        if image_file and image_file.filename != "":
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        posts_col.insert_one({
            "name": request.form.get("name"),
            "city": request.form.get("city").strip().lower(),
            "role": request.form.get("role"),
            "price": int(request.form.get("price")),
            "description": request.form.get("description"),
            "contact": request.form.get("contact"),
            "image": image_data,
            "created_by": session.get("user")
        })

        return redirect("/admin")

    return render_template("create.html")

# -------------------------
# EDIT
# -------------------------
@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    if not session.get("auth"):
        return redirect("/login")

    post = posts_col.find_one({"_id": ObjectId(id)})

    if not post or post.get("created_by") != session.get("user"):
        return "Unauthorized"

    if request.method == "POST":
        image_file = request.files.get("image")

        update_data = {
            "name": request.form.get("name"),
            "city": request.form.get("city").strip().lower(),
            "role": request.form.get("role"),
            "price": int(request.form.get("price")),
            "description": request.form.get("description"),
            "contact": request.form.get("contact"),
        }

        if image_file and image_file.filename != "":
            update_data["image"] = base64.b64encode(image_file.read()).decode("utf-8")

        posts_col.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        return redirect("/admin")

    return render_template("edit.html", post=post)

# -------------------------
# DELETE
# -------------------------
@app.route("/delete/<id>")
def delete(id):
    if not session.get("auth"):
        return redirect("/login")

    posts_col.delete_one({
        "_id": ObjectId(id),
        "created_by": session.get("user")
    })

    return redirect("/admin")

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    create_admin()
    app.run(debug=True)