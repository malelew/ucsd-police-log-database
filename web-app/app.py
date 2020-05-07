import json
from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('APP_CONFIG_FILE', silent=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

with open("./src/initial_pull.json", "r") as file:
    full_data = json.load(file)

@app.route("/")
def index():
  # return render_template("./index.html", data=full_data)
  return render_template("./triton_news_header.html", data=full_data)
