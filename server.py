from flask import Flask, render_template, redirect, request, session, flash, jsonify
from flask_bcrypt import Bcrypt   
from mysqlconnection import connectToMySQL
from datetime import date, datetime

import datetime
import re   # "re"regular expression operations
import pymysql
import pymysql.cursors #makes data sent as python dictionaries

mysql = connectToMySQL('registrationsdb')

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
    mysql = connectToMySQL('recipesdb')
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
    mysql = connectToMySQL('recipesdb')
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
        mysql = connectToMySQL('recipesdb')
        pw_hash = bcrypt.generate_password_hash(request.form['password']) 

        query = "INSERT INTO users (user_name, email, password_hash, birthdate, created_at, updated_at) VALUES (%(user_name)s, %(email)s, %(password_hash)s, %(birthdate)s, NOW(), NOW());"
        data = {
             "user_name": request.form['username'],
             "email": request.form['email'],
             "password_hash": pw_hash,
             "birthdate": request.form['birthday']
        }
        new_user_id=mysql.query_db(query, data)

        # get user_id and store into session
        session['user_id'] = new_user_id
        session['user_name'] = request.form['username']
    
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
    mysql = connectToMySQL('recipesdb')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email'] }
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['password_hash'], request.form['password']):
            
            # if True: store some user data in session
            session['user_id'] = result[0]['id']
            session['user_name'] = result[0]['user_name']
    
            return redirect("/getReviews")
    
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


# # =====================================================
# #                 DASHBOARD card : create
# # =====================================================

# @app.route('/create', methods=['GET'])
# def create():
#     user_id= session['user_id']
#     return render_template('create.html', user_id = user_id)



# # =====================================================
# #                 DASHBOARD card : review
# # =====================================================
# @app.route('/review', methods=['GET'])
# def review():
#     user_id= session['user_id']

#     mysql = connectToMySQL('recipesdb')
#     query = "SELECT * FROM recipes WHERE user_id = %(user_id)s;"
#     data = {
#         "user_id": user_id
#     }
#     result = mysql.query_db(query, data)

#     print("***** RESULT:", result)

#     return render_template('review.html', user_id = user_id, recipes = result)


# # =====================================================
# #               button ROUTE: /createRecipe
# # =====================================================
# @app.route('/createRecipe', methods=['POST', 'GET'])
# def createRecipe():
#     user_id = session['user_id']

#     mysql = connectToMySQL('recipesdb')
#     query = "INSERT INTO recipes (name, description, instructions, cook_time, created_at, updated_at, user_id) VALUES (%(name)s, %(description)s, %(instructions)s, %(cook_time)s, NOW(), NOW(), %(user_id)s);"
#     data = {
#         "name": request.form['recipeName'],
#         "description": request.form['description'],
#         "instructions": request.form['instructions'],
#         "cook_time": request.form['cook_time'],
#         "user_id": user_id
#     }

#     mysql.query_db(query, data)

#     flash("YOU CREATED A RECIPE, HOPE IT'S GOOD!", 'success')

#     return redirect('/create')


# # =====================================================
# #                 DELETE A RECIPE
# # =====================================================
# @app.route('/delete', methods=['POST'])
# def delete():
#     mysql = connectToMySQL('recipesdb')
#     query = "DELETE FROM recipes WHERE (id = %(id)s);"
#     data = {
#         'id': request.form['recipeID']
#     }
    
#     mysql.query_db(query, data)

#     return redirect('/review')



# # =====================================================
# #                 RECIPE INSTRUCTIONS
# # =====================================================
# @app.route('/instructions', methods=['POST'])
# def instructions():
#     user_id = session['user_id']

#     mysql = connectToMySQL('recipesdb')
#     query = "SELECT id, name, description, instructions, cook_time FROM recipes WHERE (recipes.id = %(id)s);"
#     data = {
#         'id': request.form['recipeID']
#     }

#     result = mysql.query_db(query, data)

#     print('***** INSTRUCTIONS RESULT:', result)

#     return render_template('instructions.html', recipe = result)


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



