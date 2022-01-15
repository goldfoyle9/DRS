import os
import random

from flask import Flask, render_template, flash, request, session
from wtforms import Form, StringField, TextAreaField, PasswordField, validators

import dbconnection
from classes.HelperClasses import Temp
from dbconnection import connection

TEMPLATE_DIR = os.path.abspath('../templates')
STATIC_DIR = os.path.abspath('../static')

# app = Flask(__name__) # to make the app run without any
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app = Flask(__name__)
app.secret_key = 'any random string'


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
            session['email'] = temp[2]
            res = Temp(temp[0] + ' ' + temp[1], temp[8] is not None)
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
                       "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (
                       result['name'], result['lastName'], result['email'], result['address'], result['city'],
                       result['country'], result['psw'], result['phone']))
        conn.commit()
        cursor.close()
        conn.close()
    return render_template("login.html", result=result)


@app.route('/edit_profile', methods=["GET"])
def get_profile_information(temp=None):
    conn = dbconnection.connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email= %s", (session['email']))
    row = cursor.fetchone()
    temp.name = row[0]
    temp.lastname = row[1]
    temp.email = row[2]
    temp.address = row[3]
    temp.city = row[4]
    temp.country = row[5]
    temp.phoneNumber = row[6]
    cursor.close()
    conn.close()
    return render_template("modify_account.html", result=temp)


def modify_profile(params, temp=None):
    conn = dbconnection.connection()
    cursor = conn.cursor()
    cursor.execute("Update Users SET firstname=%s, lastname=%s, address=%s, city=%s, country=%s, passwrd=%s, "
                   "phoneNumber=%s WHERE email=%s", params.firstname, params.lastname, params.address, params.city,
                   params.country, params.passwrd, params.phoneNumber, session['email'])

    conn.commit()
    cursor.close()
    conn.close()
    temp.name = params.firstname
    temp.lastname = params.lastname
    temp.address = params.address
    temp.city = params.city
    temp.country = params.country
    temp.phoneNumber = params.phoneNumber
    return render_template("modify_account.html", result=temp)


def link_card(params):
    conn = dbconnection.connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Cards (card_num, exp_date, cvc_code, balance) VALUES (%s, %s, %s, %s)", params.card_num,
                   params.exp_date, params.cvc_code, random.randrange(1, 100000, 1))

    cursor.execute("UPDATE Users SET card_num=%s WHERE email=%s", params.card_num, session['email'])

    conn.commit()
    cursor.close()
    conn.close()
    return render_template("index.html")

def verify_account(params):
    conn = dbconnection.connection()
    cursor = conn.cursor()
    cursor.execute("select * from cards where cards.card_num = (select card_num from users where email=%s)",
                   session['email'])
    row = cursor.fethcone()
    cursor.execute("update cards set balance=%s where card_num=%s", row[3] - 1, row[0])
    conn.commit()
    cursor.close()
    conn.close()
    return

def transfer_funds_to_online(funds):
    conn = dbconnection.connection()
    cursor = conn.cursor()
    cursor.execute("select * from cards where cards.card_num = (select card_num from users where email=%s)",
                   session['email'])
    row = cursor.fetchone()



    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
