import os
from flask import Flask, render_template, flash, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from dbconnection import connection


TEMPLATE_DIR = os.path.abspath('../templates')
STATIC_DIR = os.path.abspath('../static')

# app = Flask(__name__) # to make the app run without any
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app = Flask(__name__)

@app.route("/")
def main():
    return render_template('index.html')


@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')




"""
@app.route('/login', methods = ["GET", "POST"])
def login_page():
    error = None
    try:
        if request.method == "POST":
            attempted_username = request.form["username"]
            attempted_password = request.form["password"]



            flash(attempted_username)
            flash(attempted_password)

    except Exception as e:
        flash(e)
        return render_template("login.html", error = error)
"""


class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    lastname = StringField('Last Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    address = StringField('Address', [validators.Length(min=6, max=50)])
    city = StringField('City', [validators.Length(min=2, max=50)])
    password = PasswordField('Password', validators.DataRequired(), validators.length(min=6, max=15))



@app.route('/register', methods=["GET", "POST"])
def register_page():
    if request.method == 'POST':
        result = request.form
        


    return render_template("proba.html", result=result)




if __name__ == "__main__":
    app.run(port=5000)

