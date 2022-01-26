from DRS.config import db, ma
from time import sleep

def login_return(email, password, mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email= %s AND passwrd= %s", (email, password))
    return cursor.fetchone()

def register(params, mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users(firstname, lastname, email, address, city, country, passwrd, phoneNumber) "
                   "VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (
                       params['name'], params['lastName'], params['email'], params['address'], params['city'],
                       params['country'], params['psw'], params['phone']))
    conn.commit()
    cursor.close()
    conn.close()
    return

def modify(params, mysql, email):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("UPDATE Users SET firstname=%s, lastname=%s, address=%s, city=%s, country=%s, passwrd=%s, "
                   "phoneNumber=%s WHERE email=%s",
                   (params['name'], params['lastName'], params['address'], params['city'],
                    params['country'], params['psw'], params['phone'], email))
    conn.commit()
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
