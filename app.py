SHEET_URL = "https://docs.google.com/spreadsheets/d/1L2lH4dS1DJ0CDU3nPxK1FDMy_v3OwSbZjta2t967Eac/export?format=csv"
from flask import Flask, render_template, request
import pandas as pd
import time

app = Flask(__name__)


def get_posts():
    url = SHEET_URL + "&t=" + str(time.time())
    df = pd.read_csv(url)

    # Clean columns
    df.columns = df.columns.str.strip()

    # Rename messy Google Form columns
    df = df.rename(columns={
        "Role (Dropdown)": "Role",
        "Price (Number)": "Price",
        "Description (Paragraph)": "Description"
    })

    # Drop empty rows
    df = df.dropna(how="all")

    # Normalize
    df["City"] = df["City"].astype(str).str.strip().str.lower()
    df["Role"] = df["Role"].astype(str).str.strip()

    return df.to_dict(orient="records")


@app.route("/")
def home():
    posts = get_posts()

    city = request.args.get("city", "").lower()
    role = request.args.get("role", "")

    if city:
        posts = [p for p in posts if city in p.get("City", "")]

    if role:
        posts = [p for p in posts if p.get("Role") == role]

    posts = posts[::-1]  # latest first

    return render_template("index.html", posts=posts, city=city, role=role)


if __name__ == "__main__":
    app.run(debug=True)