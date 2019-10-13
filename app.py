from flask import Flask, flash, session, render_template, redirect, url_for, request
import sqlite3 as sql
import subprocess, random
import os
from subprocess import check_output
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Regexp, Length, NumberRange

app = Flask(__name__)
app.secret_key = 'asdfafhya78eh38w47hg3i4ra'

@app.route("/")
def index():
   #if logged in, send to spell check form, otherwise send to login
   if 'username' in session and session['is_authenticated']: 
      return redirect(url_for('spell_check'))
   
   return redirect(url_for('login'))

@app.route("/spell_check", methods = ['POST', 'GET'])
def spell_check():
   if 'username' in session and session['is_authenticated']: 
      username = session['username']
      form = SpellForm()
      if form.validate_on_submit():
         text = form.inputtext.data
         #set textout field to be input text
         form.textout.data = form.inputtext.data
         form.inputtext.data = ""

         #define filename to include username and a random number
         filename = username+'-'+str(random.randint(1, 1000))+'.txt'

         #create file and set output of check_words to misspelled input text
         with open(filename, 'w') as f:
            f.write(str(text))
            f.close()
            if os.path.isfile(filename):
               form.misspelled.data = check_words(filename)
               os.remove(filename)
            else:
               print("Error: %s file not found" % filename)            

      return render_template("spell_check.html", username = username, form = form)
   else:
      return redirect(url_for('login'))

@app.route('/register', methods = ['POST', 'GET'])
def register():
   if 'username' in session and session['is_authenticated']: 
      return redirect(url_for('spell_check'))

   form = UserRegisterForm()
   form_type = "Register"
   if form.validate_on_submit():
      username = form.uname.data
      password = form.pword.data
      pin = form.pin.data
      with sql.connect("database.db") as con:
         cur = con.cursor()
         if username != '' and password != '' and pin != '':
            con.row_factory = sql.Row
            cur.execute("SELECT * FROM users WHERE username = ? ",[username])
            rows = cur.fetchall()
            if len(rows) >= 1:
               flash("Failure: Account already exists. Please login or select a different username.","success")
               return redirect(url_for('login'))  
            else:
               password = generate_password_hash(password)
               # pin = generate_password_hash(pin)
               cur.execute("INSERT INTO users (username,password,pin) VALUES (?,?,?)",(username,password,pin))
               
               con.commit()
               # session['username'] = username
               flash("Success: Account registered!","success")
               return redirect(url_for('login'))  
         else:
            flash("Failure: Invalid account details. Please try again.","success")
         con.close()
   return render_template("form.html", type = form_type, form = form)

@app.route('/login', methods = ['POST', 'GET'])
def login():
   if 'username' in session: 
      if session['is_authenticated']:  
         return redirect(url_for('spell_check'))
      else:
         form = User2FAForm()
         form_type = '2FA'
         if form.validate_on_submit():
            username = session['username']
            pin = form.pin.data
            
            con = sql.connect("database.db")
            con.row_factory = sql.Row
            
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?",[username] )
            
            rows = cur.fetchall()
            con.close()

            if len(rows) >= 1 and rows[0]['pin'] == pin:
               session['is_authenticated'] = True
               flash("Success: You are logged in!","result")
               return redirect(url_for('spell_check'))       
            else:
               flash("Two-factor failure. Please try again.","result")            
   else:      
      form = UserLoginForm()
      form_type = 'Login'
      if form.validate_on_submit():
         
         username = form.uname.data
         password = form.pword.data
         
         con = sql.connect("database.db")
         con.row_factory = sql.Row
         
         cur = con.cursor()
         cur.execute("SELECT * FROM users WHERE username = ?",[username] )
         
         rows = cur.fetchall()
         con.close()

         if len(rows) >= 1 and check_password_hash(rows[0]['password'],password):
            session['username'] = username
            session['is_authenticated'] = False  
            form = User2FAForm()
            form_type = '2FA'   
         else:
            flash("Incorrect username or password. Please try again.","result")
         
   return render_template("form.html", type = form_type, form = form)      

@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   session.pop('is_authenticated', None)
   return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
   return redirect(url_for('index'))

def check_words(filename):
    stdout = check_output(['./a.out',filename, 'wordlist.txt']).decode('utf-8').replace('\n',', ')[:-2]
    return stdout

class UserRegisterForm(FlaskForm):
   uname = StringField('Username', validators=[DataRequired(), Regexp(r'^[\w.@+-]+$'), Length(min=4, max=25)])
   # pword = PasswordField('Password', validators=[DataRequired(), Length(min=12)])
   pword = PasswordField('Password', validators=[DataRequired()])
   pin = IntegerField('Two-Factor Authentication', validators=[DataRequired(), NumberRange(min=1000000000,max=9999999999)], id='2fa')
   # pin = StringField('Two-Factor Authentication', validators=[DataRequired()], id='2fa')
   submit = SubmitField('Submit')

class UserLoginForm(FlaskForm):
   uname = StringField('Username', validators=[DataRequired(), Regexp(r'^[\w.@+-]+$')])
   pword = PasswordField('Password', validators=[DataRequired()])
   submit = SubmitField('Submit')

class User2FAForm(FlaskForm):
   pin = IntegerField('Two-Factor Authentication', validators=[DataRequired(), NumberRange(min=1000000000,max=9999999999)], id='2fa')
   # pin = StringField('Two-Factor Authentication', validators=[DataRequired()], id='2fa')
   submit = SubmitField('Submit')

class SpellForm(FlaskForm):
   inputtext = TextAreaField('Text', validators=[DataRequired()], id="inputtext", render_kw={"rows": 4, "cols": 100})
   textout = TextAreaField('Text out', id="textout", render_kw={"disabled": "disabled", "rows": 4, "cols": 100})
   misspelled = TextAreaField('Misspelled', id="misspelled", render_kw={"disabled": "disabled", "rows": 4, "cols": 100})
   submit = SubmitField('Submit')

if __name__ == '__main__':
   app.run(debug = True)