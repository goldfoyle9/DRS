import os
from flask import Flask, render_template, flash, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators

import dbconnection
from dbconnection import connection


TEMPLATE_DIR = os.path.abspath('../templates')
STATIC_DIR = os.path.abspath('../static')

# app = Flask(__name__) # to make the app run without any
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app = Flask(__name__)

@app.route("/")
def main():
    return render_template('login.html')

@app.route("/login_redirect", methods=["GET"])
def login_redirect():
    return render_template('login.html')

@app.route("/register_redirect", methods=["GET"])
def register_redirect():
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['psw']

        conn = connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email= %s AND passwrd= %s", (email, password))
        temp = cursor.fetchone()
        if (temp):
            res = temp[0] + ' ' + temp[1]
            return render_template('index.html', result=res)
        else:
            flash("error, wrong password")

@app.route('/register', methods=["GET", "POST"])
def register_page():
    if request.method == 'POST':
        result = request.form
        conn = dbconnection.connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users(firstname, lastname, email, address, city, country, passwrd, phoneNumber) "
                       "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (result['name'], result['lastName'], result['email'], result['address'], result['city'], result['country'], result['psw'], result['phone']))
        conn.commit()
        cursor.close()
        conn.close()
    return render_template("login.html", result=result)

if __name__ == "__main__":
    app.run(port=5000)

