from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re
from flask.ext.bcrypt import Bcrypt
app = Flask(__name__)
app.secret_key = "ThisIsSecret!"
bcrypt = Bcrypt(app)
mysql = MySQLConnector(app,'thewall')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
PASSWORD_REGEX = re.compile('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?!.*\s).{4,8}$')
NAMES_REGEX = re.compile('^[a-zA-Z]+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
    if len(request.form['first_name']) < 1:
        flash("First Name cannot be blank!")
        return redirect('/')
    elif not NAMES_REGEX.match(request.form['first_name']):
        flash("Sorry, there may be Invalid characters in First Name field!")
        return redirect('/')

    if len(request.form['last_name']) < 1:
        flash("Last Name cannot be blank!")
        return redirect('/')
    elif not NAMES_REGEX.match(request.form['last_name']):
        flash("Sorry, there may be Invalid characters in Last Name field!")
        return redirect('/')

    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        return redirect('/')
    elif not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!")
        return redirect('/')

    if len(request.form['password']) < 1:
        flash("Password cannot be blank!")
        return redirect('/')
    elif not PASSWORD_REGEX.match(request.form['password']):
        flash("Invalid Password!")
        return redirect('/')
    else:
        password = bcrypt.generate_password_hash(request.form['password'])

    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"
    data = {
        'first_name' : request.form['first_name'],
        'last_name' : request.form['last_name'],
        'email' : request.form['email'],
        'password' : password,
    }
    user = mysql.query_db(query, data)
    session['user_id'] = user
    return redirect('/wall')

@app.route('/login', methods = ['POST'])
def retrieve():
    email = request.form['log_email']
    password = request.form['log_password']
    if len(email) < 1:
        flash("Email cannot be blank!")
        return redirect('/')
    elif not EMAIL_REGEX.match(email):
        flash("Invalid Email Address!")
        return redirect('/')
    else:
        query = "SELECT email FROM users WHERE email = :email"
        data = {
            'email' : request.form['log_email']
        }
        check = mysql.query_db(query, data)
        if check == request.form['log_email']:
            return True
        else:
            flash("sorry no email match")

    query = "SELECT id, password FROM users WHERE email = :email"
    data = {
        'email' : request.form['log_email']
    }
    user = mysql.query_db(query, data)
    print user
    print user[0]['password']

    if bcrypt.check_password_hash(user[0]['password'], password):
        print user[0]['password']
        session['user_id'] = user[0]['id']
        return redirect('/wall')
    else:
        flash("Invalid login recieved!")
        return redirect("/")

@app.route('/messages/<user_id>', methods = ['POST'])
def messages(user_id):
    print session['user_id']
    query = "INSERT INTO messages (users_id, message, created_at, updated_at ) VALUES (:users_id, :message, NOW(), NOW())"
    data = {
        'users_id' : session['user_id'],
        'message' : request.form['message']
    }
    message_id = mysql.query_db(query, data)

    return redirect('/wall')

@app.route('/comments/<message_id>', methods = ['POST'])
def comments(message_id):
    session['message_id'] = message_id
    query = "INSERT INTO comments (users_id, messages_id, comment, created_at, updated_at ) VALUES (:users_id, :messages_id, :comment, NOW(), NOW())"
    data = {
        'users_id' : session['user_id'],
        'messages_id' : message_id,
        'comment' : request.form['comment']
    }
    comment = mysql.query_db(query, data)
    print message_id

    commessage_query = "SELECT  comments.users_id, comments.id, comments.comment, comments.created_at, comments.updated_at FROM comments JOIN messages ON comments.messages_id = messages.id WHERE messages_id = :id"
    commessage_data = {
        'id' : message_id
    }
    print message_id
    messages_comments = mysql.query_db(commessage_query, commessage_data)

    return redirect('/wall')

@app.route('/wall')
def show():
    user_id = session.get('user_id', None)
    print user_id
    query = "SELECT CONCAT_WS(' ', users.first_name, users.last_name) AS full_name FROM users WHERE id = :id"
    data = {
        'id' : user_id
    }
    user = mysql.query_db(query, data)
    print user_id

    m_query = "SELECT CONCAT_WS(' ', users.first_name, users.last_name) AS full_name, messages.users_id, messages.id, messages.message, messages.created_at, messages.updated_at FROM messages JOIN users ON messages.users_id = users.id"

    user_messages = mysql.query_db(m_query)
    print user_messages

    c_query = "SELECT CONCAT_WS(' ', users.first_name, users.last_name) AS full_name, comments.users_id, comments.id, comments.comment,comments.messages_id, comments.created_at, comments.updated_at FROM comments JOIN users ON comments.users_id = users.id WHERE users_id = :id"
    c_data = {
        'id' : user_id
    }
    user_comments = mysql.query_db(c_query, c_data)
    print user_comments, "This is the user comments"

    message_id = session.get('message_id')
    print message_id
    commessage_query = "SELECT comments.users_id, comments.id, comments.comment, comments.messages_id, comments.created_at, comments.updated_at, messages.id FROM comments JOIN messages ON comments.messages_id = messages.id WHERE messages_id = :id"
    commessage_data = {
        'id' : message_id
    }

    messages_comments = mysql.query_db(commessage_query, commessage_data)
    print messages_comments
    print message_id


    return render_template('wall.html', users = user[0], user_id = user_id, messages = user_messages, user_comments = user_comments, mess_comments = messages_comments)

@app.route('/wall/userlog_out/')
def logout():
    session.clear()
    return redirect('/')

@app.route('/wall/delete') #this is broke. Plan on coming back later.
def delete():
    return redirect('')

app.run(debug=True)
