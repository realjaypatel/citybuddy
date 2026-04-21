from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "secret123"  # simple session key

# -------------------------
# HARD-CODED MongoDB URI
# -------------------------
MONGO_URI = "mongodb+srv://user:user@cluster0.u3fdtma.mongodb.net/citybuddy?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["hf"]

posts_col = db["posts"]
users_col = db["users"]


# -------------------------
# INIT ADMIN (run once)
# -------------------------
def create_admin():
    if users_col.count_documents({}) == 0:
        users_col.insert_one({
            "username": "admin",
            "password": "admin123"   # plain text (as you asked)
        })


# -------------------------
# HOME
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
# LOGIN (plain text)
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = users_col.find_one({
            "username": request.form.get("username"),
            "password": request.form.get("password")
        })

        if user:
            session["auth"] = True
            return redirect("/admin")

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
# CREATE POST
# -------------------------
@app.route("/create", methods=["GET", "POST"])
def create():
    if not session.get("auth"):
        return redirect("/login")

    if request.method == "POST":
        posts_col.insert_one({
            "name": request.form.get("name"),
            "city": request.form.get("city").lower(),
            "role": request.form.get("role"),
            "price": int(request.form.get("price")),
            "description": request.form.get("description"),
            "contact": request.form.get("contact")
        })

        return redirect("/admin")

    return render_template("create.html")


# -------------------------
# DELETE POST
# -------------------------
@app.route("/delete/<id>")
def delete(id):
    if not session.get("auth"):
        return redirect("/login")

    posts_col.delete_one({"_id": ObjectId(id)})
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