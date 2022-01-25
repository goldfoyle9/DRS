import os
import random

import requests as requests

import response

from flask import Flask, render_template, flash, request, session, url_for
from werkzeug.utils import redirect

from config import db, ma
from flaskext.mysql import MySQL

from classes.HelperClasses import Temp

TEMPLATE_DIR = os.path.abspath('../templates')
STATIC_DIR = os.path.abspath('../static')

# app = Flask(__name__) # to make the app run without any
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app = Flask(__name__)
app.secret_key = 'any random string'

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'drs_db'
# app.config['MYSQL_DATABASE_HOST'] = 'db' #za docker
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@mysql:3306/drs_db'
db.init_app(app)
ma.init_app(app)


@app.route("/")
def main():
    return render_template('login.html')


@app.route("/login_redirect", methods=["GET"])
def login_redirect():
    return render_template('login.html')


@app.route("/register_redirect", methods=["GET"])
def register_redirect():
    return render_template('register.html')


@app.route("/edit_redirect", methods=["GET"])
def edit_redirect():
    return render_template('modify_account.html')


@app.route("/index_redirect", methods=["GET", "POST"])
def index():
    return render_template('index.html')

@app.route("/add_card_redirect", methods=["GET", "POST"])
def add_card_redirect():
    return render_template('add_card.html')

@app.route("/add_balance_redirect", methods=["GET", "POST"])
def add_balance_redirect():
    return render_template('add_balance.html')

@app.route("/get_transactions_redirect", methods=["GET"])
def get_transactions_redirect():
    return render_template("transactions.html")

@app.route("/send_transaction_redirect", methods=["GET", "POST"])
def send_transaction_redirect():
    return render_template("send_transaction.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['psw']

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE email= %s AND passwrd= %s", (email, password))
        temp = cursor.fetchone()
        if (temp):
            session['email'] = temp[2]
            session['name'] = temp[0]
            res = Temp(temp[0] + ' ' + temp[1], temp[8] is not None)
            return render_template('index.html', result=res)
        else:
            flash("errorrrr, wrong password")


@app.route('/register', methods=["GET", "POST"])
def register_page():
    if request.method == 'POST':
        result = request.form
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users(firstname, lastname, email, address, city, country, passwrd, phoneNumber) "
                       "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (
                           result['name'], result['lastName'], result['email'], result['address'], result['city'],
                           result['country'], result['psw'], result['phone']))
        conn.commit()
        cursor.close()
        conn.close()
    return render_template("login.html", result=result)



def get_profile_information(temp):
    conn = mysql.connect()
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
    return temp



@app.route('/modify_profile', methods=["GET", "POST"])
def modify_profile(temp=None):
    conn = mysql.connect()
    cursor = conn.cursor()
    result = request.form
    cursor.execute("UPDATE Users SET firstname=%s, lastname=%s, address=%s, city=%s, country=%s, passwrd=%s, "
                   "phoneNumber=%s WHERE email=%s", (result['name'], result['lastName'], result['address'], result['city'],
                   result['country'], result['psw'], result['phone'], session['email']))

    conn.commit()
    cursor.close()
    conn.close()

    session['name'] = result['name']

    return render_template("index.html", result=result)


@app.route('/check_balance', methods=["POST", "GET"])
def check_balance():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=%s",
                   session['email'])

    row = cursor.fetchone()
    dinari = row[9]
    response = requests.get('http://api.exchangeratesapi.io/v1/latest?access_key=fba506b7b878a42746e79023db275313')
    valute = response.json()['rates']
    euri = dinari/valute['RSD']
    dolari = euri*valute['USD']
    jeni = euri*valute['JPY']
    aud = euri*valute['AUD']
    gbp = euri*valute['GBP']
    result = [dinari, euri, dolari, jeni, aud, gbp]

    conn.close()
    return render_template('balance.html', result=result)


@app.route('/add_card', methods=["GET", "POST"])
def link_card():
    if request.method == 'POST':
        result = request.form
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("select * from Cards where card_num=%s", result['card_num'])
        row = cursor.fetchone()
        if(row):
            cursor.execute("update Users set card_num=%s where email=%s", (result['card_num'], session['email']))
            #baciti neki eror

        conn.commit()
        cursor.close()
        conn.close()
        verify_account()


    return render_template("index.html")


def verify_account():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("select * from Cards where Cards.card_num = (select card_num from Users where email=%s)",
                   session['email'])
    row = cursor.fetchone()
    response = requests.get('http://api.exchangeratesapi.io/v1/latest?access_key=fba506b7b878a42746e79023db275313')
    valute = response.json()['rates']
    dinari = valute['RSD']
    dolari = valute['USD']
    cursor.execute("update Cards set balance=%s where card_num=%s", (row[3] - dinari/dolari, row[0]))
    conn.commit()
    cursor.close()
    conn.close()
    return

@app.route('/add_balance', methods = ["GET", "POST"])
def add_balance():
    if request.method == "POST":
        result = request.form
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("select * from Cards where Cards.card_num = (select card_num from Users where email=%s)",
                       session['email'])
        row = cursor.fetchone()
        balance = row[3]
        form_amount = int(result['balance'])

        if(balance >= form_amount):
            cursor.execute("UPDATE Cards set balance=%s where card_num=%s", (balance - form_amount, row[0]))
            cursor.execute("update Users set balance=balance+%s where email=%s", (form_amount, session['email']))
        else:
            print("Nije moguce")

        conn.commit()
        cursor.close()
        conn.close()
        return render_template("index.html")

@app.route('/get_transactions', methods= ["GET", "POST"])
def get_transactions():

    conn= mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * from Transactions where email=%s", session['email'])
    data = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    return render_template("transactions.html", transactions = data)

@app.route('/send_transaction', methods=["GET", "POST"])
def send_transaction():
    if request.method == "POST":
        result = request.form
        conn = mysql.connect()
        cursor = conn.cursor()
        Failed = "None"
        cursor.execute("select * from Users where email=%s", session['email'])
        row = cursor.fetchone()
        valuta= result['valuta']
        response = requests.get('http://api.exchangeratesapi.io/v1/latest?access_key=fba506b7b878a42746e79023db275313')
        valute = response.json()['rates']
        dinar = valute['RSD']
        euro = float(result['amount'])/valute[valuta]
        iznos = dinar*euro
        if(row[9]>=iznos):
            cursor.execute("update Users set balance=%s where email=%s", (row[9]-iznos, session['email']))
            cursor.execute("select * from Users where email=%s", result['emailTo'])
            user = cursor.fetchone()
            if (user[8]):
                cursor.execute("update Users set balance=balance+%s where email=%s",(iznos, result['emailTo']) )
                cursor.execute("insert into Transactions (email, amount, emailTo) VALUES(%s, %s, %s)",
                               (session['email'], iznos, result['emailTo']))
            else:
                cursor.execute("insert into Transactions (email, amount, emailTo) VALUES(%s, %s, %s)",
                               (session['email'],iznos, Failed))
        else:
            print("Nema para")
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('get_transactions'))

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')
