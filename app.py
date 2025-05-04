from flask import Flask, render_template, request, redirect, url_for, session, flash
# mysql connector 
import mysql.connector

# Database connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="capstone_v1"
)
db_cursor = db_connection.cursor()

app = Flask(__name__)

@app.route('/') 
def home():
    # handle login and registration logic, role based admin and user
    
    
    return render_template('index.html')

# playground.html
@app.route('/playground')
def playground():
    return render_template('playground.html')

# -------------------------------------------------------ADMIN------------------------------------------------------------------- #
# admin>dashboard.html
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)