import sqlite3

conn = sqlite3.connect('database.db')
print("Opened database successfully")

conn.execute('CREATE TABLE users (username TEXT, password TEXT, pin INTEGER)')
print("Table created successfully")
conn.close()