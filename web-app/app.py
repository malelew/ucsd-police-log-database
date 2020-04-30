from flask import Flask, render_template, redirect

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('APP_CONFIG_FILE', silent=True)

@app.route("/")
def index():
  return render_template("./triton_news_header.html")