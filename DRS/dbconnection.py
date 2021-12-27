import mysql.connector

def connection():
    connection = mysql.connector.connect(user='root', password='loltyler1', host='127.0.0.1', database='drs_db')

    return connection
