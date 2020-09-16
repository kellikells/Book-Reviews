from flask import Flask, render_template, redirect, request, session, flash, jsonify, url_for
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
            return redirect('/booksPage')
    
        # if username & password don't match
        # --------------------------------------
        else:
            flash("You could not be logged in", 'login')
            return redirect("/")



# ====================================================
#               /addPage: add.html
# ====================================================
@app.route('/addPage', methods=['GET'])
def addPage():
    user_id= session['user_id']

    mysql = connectToMySQL('booksdb')
    query = "SELECT * FROM authors;"
    author_results = mysql.query_db(query)

    return render_template('add.html', author_results = author_results)


# ====================================================
#        CREATE REVIEW: insert into database
# ====================================================

@app.route('/addReview', methods=['POST']) 
def addReview():
    user_id = session['user_id']


    # validation of all inputs 
    if len(request.form['title']) < 1:
        flash("title cannot be empty", 'title')
    
    if len(request.form['new-author']) < 1 and request.form['old-author'] == "Choose":
        flash("author must be selected", 'author')

    if len(request.form['new-author']) > 0 and request.form['old-author'] != "Choose":
        flash("can't add a new author and select an author at the same time", 'author')
    
    if len(request.form['content']) < 1:
        flash("review content cannot be empty", 'review')

    if request.form['rating'] == "Choose":
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
    

    # if using dropdown for author selection 
    elif request.form['old-author']:
        # ---------  add book to database
        # =====================================
        mysql = connectToMySQL('booksdb')
        query = "INSERT INTO books (author_id, title, created_at, updated_at) VALUES (%(author_id)s, %(title)s, NOW(), NOW());"
        data = {
            'author_id': request.form['old-author'],
            'title': request.form['title']
        }

        # saving book id
        new_book = mysql.query_db(query,data)

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

# ====================================================
#           ADD REVIEW FROM bookreview.html
# ====================================================
@app.route('/additionalReview/<bookId>', methods=['POST'])
def additionalReview(bookId):
    user_id = session['user_id']


    if len(request.form['content']) < 1:
        flash("review content cannot be empty", 'review')

    if request.form['rating'] == "Choose":
        flash("select a rating", 'rating')

    # initiate any flash messages on bookreview.html
    # --------------------------------------
    if '_flashes' in session.keys():
        return redirect('/get_book_review/'+ bookId)

    else:
        mysql = connectToMySQL('booksdb')
        query = "INSERT INTO reviews (book_id, user_id, content, rating, created_at, updated_at) VALUES (%(book_id)s, %(user_id)s, %(content)s, %(rating)s, NOW(), NOW());"
        data = {
            'book_id': bookId,
            'user_id': user_id,
            'content': request.form['content'],
            'rating': request.form['rating']
        }
        mysql.query_db(query,data)

        flash("Thank you! your review is appreiated!", 'review-success')

        return redirect('/get_book_review/'+ bookId)

    # return redirect('/booksPage')
# ====================================================
#           /booksPage: books.html (home)
# ====================================================
@app.route('/booksPage', methods=['GET'])
def booksPage():
    user_id = session['user_id']

    # reviews join users, join books, join authors
    mysql = connectToMySQL('booksdb')
    query = "SELECT * FROM reviews LEFT JOIN users ON reviews.user_id= users.id JOIN books ON reviews.book_id = books.id JOIN authors ON books.author_id= authors.id ORDER BY reviews.id DESC LIMIT 3;"
    results = mysql.query_db(query)

    # getting all books in database to list as a link
    mysql = connectToMySQL('booksdb')
    query = "SELECT * FROM books;"
    book_results = mysql.query_db(query)

    return render_template('books.html', results = results, book_results = book_results)


# ====================================================
#     /get_book_review: bookreview.html
# use hidden input to get all data for specific book
# ====================================================
@app.route('/get_book_review/<bookId>', methods=['POST', 'GET'])
def getBookReview(bookId):
    user_id = session['user_id']

    # getting book title & author 
    mysql = connectToMySQL('booksdb')
    query = "SELECT books.id, author_name, title FROM books JOIN authors ON books.author_id = authors.id WHERE books.id = %(bookID)s;"
    data = {
        # 'bookID': request.form['book_id']
        'bookID': bookId
    }
    results = mysql.query_db(query, data)

    # getting reviews for the book
    mysql = connectToMySQL('booksdb')
    query = "SELECT * FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = %(bookID)s;"
    data = {
        'bookID': bookId
    }
    review_results = mysql.query_db(query, data)


    

    return render_template('bookreview.html', results = results, review_results= review_results, total = len(review_results))



# ====================================================
#            /getUser: users.html
# ====================================================
@app.route('/getUser/<userId>', methods=['POST', 'GET'])
def getUser(userId):
    user_id = session['user_id']

    # getting user data
    mysql = connectToMySQL('booksdb')
    query = "SELECT * FROM users WHERE id = %(id)s;"
    data = {
        'id': userId
    }
    user_results = mysql.query_db(query, data)


    # getting reviews by the user
    mysql = connectToMySQL('booksdb')
    query = "SELECT reviews.id,reviews.book_id,reviews.user_id,books.title FROM reviews JOIN books ON reviews.book_id=books.id WHERE reviews.user_id = %(user_id)s;"
    data = {
        'user_id': userId
    }
    review_results = mysql.query_db(query, data)


    # getting total reviews by user
    mysql = connectToMySQL('booksdb')
    query = "SELECT COUNT(id) AS count FROM reviews WHERE reviews.user_id = %(user_id)s;"
    data = {
        'user_id': userId
    }
    count_results = mysql.query_db(query, data)

    return render_template('users.html', user_results = user_results, review_results = review_results, count_results = count_results)


# ====================================================
#          DELETE A REVIEW: bookreview.html
# ====================================================
@app.route('/delete_review/<bookId>/<reviewId>', methods=['POST', 'GET'])
def delete_review(bookId, reviewId):
    user_id = session['user_id']

    print("======================================")
    print(bookId)
    print(reviewId)

    mysql = connectToMySQL('booksdb')
    query = "DELETE FROM reviews WHERE (id = %(reviewId)s);"
    data = {
        'reviewId': reviewId
    }
    results= mysql.query_db(query, data)

    print("======================================")
    print(results)

    return redirect('/get_book_review/'+ bookId)


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



