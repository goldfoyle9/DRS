import multiprocessing
import os
import random
import threading

from time import sleep
import requests as requests
from multiprocessing import Process, Lock
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
app.config['MYSQL_DATABASE_HOST'] = 'db' #za docker
#app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'
mysql.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@mysql:3306/drs_db'
db.init_app(app)
ma.init_app(app)

global send_Transaction

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
        temp = login_return(email, password, mysql)
        if (temp):
            session['email'] = temp[2]
            session['name'] = temp[0]
            res = Temp(temp[0] + ' ' + temp[1], temp[8] is not None)
            return render_template('index.html', result=res)
        else:
            return render_template('login.html', error="Nepostojeci korisnik ili nije dobar password")


@app.route('/register', methods=["GET", "POST"])
def register_page():
    if request.method == 'POST':
        result = request.form
        lock = Lock()
        P = Process(target = register, args=(result, lock))
        P.start()

    return render_template("login.html", result=result)



@app.route('/modify_profile', methods=["GET", "POST"])
def modify_profile(temp=None):
    result = request.form
    lock = Lock()
    p = Process(target = modify, args=(result, session['email'], lock))
    p.start()
    #modify(result, mysql, session['email'])

    session['name'] = result['name']

    return render_template("index.html", result=result)


@app.route('/check_balance', methods=["POST", "GET"])
def check_balance():

    row = balance_check(session['email'], mysql)
    dinari = row[9]
    response = requests.get('http://api.exchangeratesapi.io/v1/latest?access_key=fba506b7b878a42746e79023db275313')
    valute = response.json()['rates']
    euri = dinari/valute['RSD']
    dolari = euri*valute['USD']
    jeni = euri*valute['JPY']
    aud = euri*valute['AUD']
    gbp = euri*valute['GBP']
    result = [dinari, euri, dolari, jeni, aud, gbp]

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
        else:
            return render_template("add_card.html", error="Kartica ne postoji u bazi")

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
            return render_template("add_balance.html", error="Nemate dovoljno sredstava na kartici")

        conn.commit()
        cursor.close()
        conn.close()
        return render_template("index.html")

@app.route('/get_transactions', methods= ["GET", "POST"])
def get_transactions():

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * from Transactions where email=%s or emailTo=%s", (session['email'], session['email']))
    data = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    return render_template("transactions.html", transactions = data)



@app.route('/send_transaction', methods=["GET", "POST"])
def send_transaction():
    if request.method == "POST":
        result = request.form
        valuta= result['valuta']
        response = requests.get('http://api.exchangeratesapi.io/v1/latest?access_key=fba506b7b878a42746e79023db275313')
        valute = response.json()['rates']
        dinar = valute['RSD']
        euro = float(result['amount'])/valute[valuta]
        iznos = dinar*euro
        email = session['email']
        emailTo = result['emailTo']
        stanje = transaction_provera(session['email'], mysql, iznos)
        if(stanje != False):
            tr = threading.Thread(target= proces_proba, args=(email, emailTo, iznos, stanje, mysql, ))
            tr.daemon = True
            tr.start()
            #proces_proba(email, emailTo, iznos, stanje,  mysql)
            #p = Process(target=proces_proba, args=(email, emailTo, iznos, stanje, mysql, ))
            #p.daemon = True
            #p.start()
        else:
            return render_template("send_transaction.html", error="Nemate dovoljno para na racunu")

    return redirect(url_for('get_transactions'))

@app.route('/sortAsc', methods= ["GET", "POST"])
def sortAsc():

    sorted_data = sortAscending(mysql, session['email'])
    return render_template("transactions.html", transactions = sorted_data)

@app.route('/sortDesc', methods= ["GET", "POST"])
def sortDesc():

    sorted_data = sortDescending(mysql, session['email'])
    return render_template("transactions.html", transactions = sorted_data)


@app.route('/filter_from', methods= ["GET", "POST"])
def filter_from():
    transactions = filter_from_func()
    return render_template("transactions.html", transactions = transactions)


@app.route('/filter_reciever', methods=["GET", "POST"])
def filter_reciever():
    transactions = filter_receiver_func(mysql, session['email'])
    return render_template("transactions.html", transactions=transactions)



def login_return(email, password, mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email= %s AND passwrd= %s", (email, password))
    return cursor.fetchone()

def register(params, lock):
    conn = mysql.connect()
    cursor = conn.cursor()
    lock.acquire()
    cursor.execute("INSERT INTO Users(firstname, lastname, email, address, city, country, passwrd, phoneNumber) "
                   "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (
                       params['name'], params['lastName'], params['email'], params['address'], params['city'],
                       params['country'], params['psw'], params['phone']))
    conn.commit()
    lock.release()
    cursor.close()
    conn.close()
    return

def modify(params, email, lock):
    conn = mysql.connect()
    cursor = conn.cursor()
    lock.acquire()
    cursor.execute("UPDATE Users SET firstname=%s, lastname=%s, address=%s, city=%s, country=%s, passwrd=%s, "
                   "phoneNumber=%s WHERE email=%s",
                   (params['name'], params['lastName'], params['address'], params['city'],
                    params['country'], params['psw'], params['phone'], email))

    conn.commit()
    lock.release()
    cursor.close()
    conn.close()
    return

def balance_check(email, mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email=%s", email)
    a = cursor.fetchone()
    cursor.close()
    conn.close()
    return a


def link_card(mysql, result):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("select * from Cards where card_num=%s", result['card_num'])
    row = cursor.fetchone()

def transaction_provera(email, mysql, iznos):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("select * from Users where email=%s", email)
    row = cursor.fetchone()
    if (row[9] >= iznos):
        cursor.close()
        conn.close()
        return row[9]
    else:
        cursor.close()
        conn.close()
        return False


def proces_proba(email, emailTo, iznos, stanje,  mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    Failed = "None"
    cursor.execute("update Users set balance=%s where email=%s", (stanje - iznos, email))
    cursor.execute("select * from Users where email=%s", emailTo)
    user = cursor.fetchone()

    cursor.execute("insert into Transactions (email, amount, emailTo, transactionStatus) VALUES(%s, %s, %s, %s)",
                   (email, iznos, emailTo, "U obradi"))
    conn.commit()

    cursor.close()
    conn.close()

    sleep(10)

    conn = mysql.connect()
    cursor = conn.cursor()

    if (user[8]):
        cursor.execute("update Users set balance=balance+%s where email=%s", (iznos, emailTo))
        cursor.execute("update Transactions set transactionStatus=%s where emailTo=%s and amount=%s",
                       ("Uspesno", emailTo, iznos))
    else:
        cursor.execute("update Transactions set transactionStatus=%s where emailTo=%s and amount=%s",
                       ("Neuspesno", emailTo, iznos))
    conn.commit()
    cursor.close()
    conn.close()


def sortAscending(mysql, email):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * from Transactions where email=%s or emailTo=%s", (email, email))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    sorted_data = sorted(data, key=lambda tup: tup[1], reverse=False)
    return sorted_data

def sortDescending(mysql, email):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * from Transactions where email=%s or emailTo=%s", (email, email))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    sorted_data = sorted(data, key=lambda tup: tup[1], reverse=True)

    return sorted_data

def filter_receiver_func(mysql, email):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * from Transactions where email=%s or emailTo=%s", (email, email))
    data = cursor.fetchall()
    transactions = []
    for row in data:
        if row[2] == email:
            transactions.append(row)

    cursor.close()
    conn.close()
    return transactions

def filter_from_func(mysql, email):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * from Transactions where email=%s or emailTo=%s", (email, email))
    data = cursor.fetchall()
    transactions = []
    for row in data:
        if row[0] == email:
            transactions.append(row)

    cursor.close()
    conn.close()

    return transactions


def foo(q):
    q.put('hello')


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    app.run(debug=True, port=5000, host='0.0.0.0')

    q = multiprocessing.Queue()
    p = Process(target=foo, args=(q,))
    p.start()