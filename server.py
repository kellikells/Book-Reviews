from flask import Flask, render_template, redirect, request, session, flash, jsonify
from flask_bcrypt import Bcrypt   
from mysqlconnection import connectToMySQL
from datetime import date, datetime

import datetime
import re   # "re"regular expression operations
import pymysql
import pymysql.cursors #makes data sent as python dictionaries

mysql = connectToMySQL('booksdb')

# used for email validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__) 
bcrypt = Bcrypt(app)  
app.secret_key = "ThisIsSecret!"

# ==============================================================
#                     INDEX ROUTE
# ==============================================================
@app.route('/')
def index():
    mysql = connectToMySQL('booksdb')
    return render_template('index.html')

# ==============================================================
#                  REGISTER BUTTON ROUTE
# ==============================================================
@app.route('/register', methods=['POST'])
def register():

    # name validation
    # --------------------------------------
    if len(request.form['name']) < 2:
        flash("your name must be at least 2 characters", 'name')

    # alias validation: not blank
    # --------------------------------------
    if request.form['alias'] == False:
        flash("Alias can't be empty", 'alias')

    # email validation
    # --------------------------------------
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", 'email')

    # checking if email already exists in db
    # --------------------------------------
    mysql = connectToMySQL('booksdb')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email']}
    matchingEmail = mysql.query_db(query, data)

    if matchingEmail:
        flash("Email already exists", 'email')
    
    # password validation
    # --------------------------------------
    if len(request.form['password']) < 8:
        flash("password must be at least 8 characters", 'password')
    
    # confirm-password validation
    # --------------------------------------
    if request.form['password'] != request.form['confirm-password']:
        flash("passwords don't match", 'confirm-password')
    
    # initiate any flash messages on index.html
    # --------------------------------------
    if '_flashes' in session.keys():
        return redirect("/")

    # ADD NEW USER TO DATABASE : hash password
    # --------------------------------------
    else:
        mysql = connectToMySQL('booksdb')
        pw_hash = bcrypt.generate_password_hash(request.form['password']) 

        query = "INSERT INTO users (name, alias, email, password_hash, created_at, updated_at) VALUES (%(name)s, %(alias)s, %(email)s, %(password_hash)s, NOW(), NOW());"
        data = {
             "name": request.form['name'],
             "alias": request.form['alias'],
             "email": request.form['email'],
             "password_hash": pw_hash
        }
        new_user_id=mysql.query_db(query, data)

        # get user_id and store into session
        session['user_id'] = new_user_id
        session['user_alias'] = request.form['alias']
    
        print('SESSION:', session)
        flash("Aww yeah, you successfully registered.  You can now log in using the same information you provided!", 'success')

        return redirect('/')

# ========================================================
#                  LOGIN BUTTON ROUTE
# ========================================================
@app.route('/login', methods=['POST'])
def login():
    
    # check if email exists in database
    # --------------------------------------
    mysql = connectToMySQL('booksdb')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email'] }
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['password_hash'], request.form['password']):
            
            # if True: store some user data in session
            session['user_id'] = result[0]['id']
            session['user_alias'] = result[0]['alias']

            print(session)
            return redirect('/getReviews')
    
        # if username & password don't match
        # --------------------------------------
        else:
            flash("You could not be logged in", 'login')
            return redirect("/")

# =====================================================
#                 get book reviews 
# =====================================================
@app.route('/getReviews', methods=['GET'])
def getReviews():
    user_id= session['user_id']


    return render_template('books.html', user_id = user_id)

# ====================================================
#               /addPage: add.html
# ====================================================
@app.route('/addPage', methods=['GET'])
def addPage():
    user_id= session['user_id']

    return render_template('add.html')


# ====================================================
#        CREATE REVIEW: insert into database
# ====================================================

@app.route('/addReview', methods=['POST']) 
def addReview():
    user_id = session['user_id']

    # validation of all inputs 
    if len(request.form['title'])<1:
        flash("title cannot be empty", 'title')
    
    if len(request.form['new-author']) <1 and request.form['old-author'] == 0:
        flash("author must be selected or entered", 'author')
    
    if len(request.form['content'])<1:
        flash("review content cannot be empty", 'review')

    if request.form['rating'] == 0:
        flash("select a rating", 'rating')

    # initiate any flash messages 
    # --------------------------------------
    if '_flashes' in session.keys():
        return redirect("/addPage")




    # if the user typed in the input for new-author
    # then add this author to database
    if request.form['new-author']:

        # --------- adding author to db 
        # =====================================
        mysql = connectToMySQL('booksdb')
        query = "INSERT INTO authors (author_name, created_at, updated_at) VALUES (%(author_name)s, NOW(), NOW());"
        data = {
            'author_name': request.form['new-author']
        }
        # saving author id
        new_author = mysql.query_db(query,data)
        print("------------------------")
        print("NEW AUTHOR:", new_author)

        # ---------  add book to database
        # =====================================
        mysql = connectToMySQL('booksdb')
        query = "INSERT INTO books (author_id, title, created_at, updated_at) VALUES (%(author_id)s, %(title)s, NOW(), NOW());"
        data = {
            'author_id': new_author,
            'title': request.form['title']
        }

        # saving book id
        new_book = mysql.query_db(query,data)
        print("------------------------")
        print("BOOK ADDED", new_book)

        # ---------  add review to database
        # =====================================
        mysql = connectToMySQL('booksdb')
        query = "INSERT INTO reviews (book_id, user_id, content, rating, created_at, updated_at) VALUES (%(book_id)s, %(user_id)s, %(content)s, %(rating)s, NOW(), NOW());"
        data = {
            'book_id': new_book,
            'user_id': user_id,
            'content': request.form['content'],
            'rating': request.form['rating']
        }

        mysql.query_db(query,data)

        flash("Your review has been posted", 'review-success')


    return redirect('/addPage')
    # mysql = connectToMySQL('booksdb')
    # query = "INSERT INTO books (author_id created_at, updated_at, user_id) VALUES (%(message)s, NOW(), NOW(), %(user_id)s);"
    # data = {
    #     'message': request.form['PostMessage'],
    #     'user_id': user_id
    # }
    # sendMessage = mysql.query_db(query, data)
    # print("SEND MESSAGE:==================", sendMessage)

    # return render_template('TheWall.html', sendMessage = sendMessage, user_id = user_id)






# ====================================================
#           
# ====================================================


# ====================================================
#           /booksPage: books.html (home)
# ====================================================
@app.route('/booksPage', methods=['GET'])
def booksPage():
    user_id= session['user_id']

    return render_template('books.html')



# ====================================================
#        LOG OUT: clear session
# ====================================================
@app.route('/logout', methods=['POST'])
def logout():
    return redirect('/clear_session')
# ----------------------------------------
@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect('/')


# =======================================================
#         START SERVER **********
# =======================================================
if __name__ == "__main__":
    app.run(debug=True)



