import sys
import textwrap
import logging.config
import sqlite3

import bottle
import bottle_sqlite
from bottle import get, post, delete, error, abort, request, response, HTTPResponse


# conn = sqlite3.connect('users.db')
# conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username string UNIQUE NOT NULL, password string NOT NULL, emailAddress string UNIQUE)")
# conn.execute("CREATE TABLE followers (id INTEGER PRIMARY KEY, user_id string NOT NULL, user_idToFollow string NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(user_idTOFOllow) REFERENCES users(id))")

app = bottle.default_app()
app.config.load_config('./etc/users.ini')

plugin = bottle_sqlite.Plugin(app.config['sqlite.users'])
app.install(plugin)

logging.config.fileConfig(app.config['logging.config'])


def json_error_handler(res):
    if res.content_type == 'application/json':
          return res.body
    res.content_type = 'application/json'
    if res.body == 'Unknown Error.':
          res.body = bottle.HTTP_CODES[res.status_code]
    return bottle.json_dumps({'errors': res.body})


app.default_error_handler = json_error_handler


if not sys.warnoptions:
    import warnings
    for warning in [DeprecationWarning, ResourceWarning]:
          warnings.simplefilter('ignore', warning)


def query(db, sql, args=(), one=False):
    cur = db.execute(sql, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row))
          for row in cur.fetchall()]
    cur.close()

    return (rv[0] if rv else None) if one else rv


def execute(db, sql, args=()):
    cur = db.execute(sql, args)
    id = cur.lastrowid
    cur.close()

    return id


@get('/users/')
def getUsers(db):
    users = query(db, 'SELECT * FROM users')
    return {'users': users}


@get('/followers/<username>')
def getFollowers(db, username):
    followers = query(db, "SELECT userToFollow FROM followers WHERE username=\'" + username  + "\';")
    return {'followers': followers}


@post('/users')
def create_user(db):
    user = request.json

    if not user:
        abort(400)

    posted_fields = user.keys()
    required_fields = {'username', 'password', 'emailAddress'}

    if not required_fields <= posted_fields:
        abort(400, f'Missing fields: {required_fields - posted_fields}')

    try:
        user['id'] = execute(db,
                             '''INSERT INTO users(username, password, emailAddress)
                             VALUES (:username, :password, :emailAddress)''', user)

    except sqlite3.IntegrityError as e:
        abort(409, str(e))

    response.status = 201
    return user


@post('/users/<username>/password')
def checkPassword(db, username):
    password = request.json

    if not password:
        abort(400)

    posted_fields = password.keys()
    required_fields = {'password'}

    if not required_fields <= posted_fields:
        abort(400, f'Missing fields: {required_fields - posted_fields}')

    db_password = query(db, 'SELECT password FROM users WHERE username=?', [username])
    if db_password != [] and db_password[0]['password'] == password['password']:
    	response.status = 200
    	return {'Authentication': True}
    else:
    	response.status = 401
    	return {'Authentication': False}


@post('/followers/<username>/<usernameToFollow>')
def addFollower(db, username, usernameToFollow):
    user = username
    userToFollow = usernameToFollow
    if  username == userToFollow:
        response.status = 400
        return { 'Status' : response.status, 'message' : 'Cannot follow self'}
    sql = "SELECT username, userToFollow FROM followers WHERE username=\'" + user + "\' and userToFollow=\'" + userToFollow + "\';"
    c = db.execute(sql).fetchone()
    user1_sql = "SELECT username FROM users WHERE username=\'" + user  + "\';"
    d = db.execute(user1_sql).fetchall()
    user2_sql = "SELECT username FROM users WHERE username=\'" + userToFollow + "\';"
    e = db.execute(user2_sql).fetchall()
    print(e)
    print(d)
    if not d or not e:
        response.status = 400
        return { 'Status' : response.status, 'message' : 'User does not exist'}
    if not c:
        try:
            execute(db, '''INSERT INTO followers(username, userToFollow) VALUES (?, ?)''', (user, userToFollow))
            response.status = 201
            return { 'userFollowed' : userToFollow}
        except sqlite3.IntegrityError as e:
            abort(409, str(e))

    checkUser = c[0]
    checkUserToFollow = c[1]

    print(user, userToFollow)
    print(checkUser, checkUserToFollow)

    if(user == checkUser and userToFollow == checkUserToFollow):
        response.status = 409
        return { 'Status' : response.status, 'message' : 'Already following'}

@delete('/followers/<username>/<usernameToUnfollow>')
def removeFollower(db, username, usernameToUnfollow):
    user = username
    userToRemove = usernameToUnfollow
    if  username == userToRemove:
        response.status = 400
        return { 'Status' : response.status, 'message' : 'Cannot unfollow self'}
    sql = "SELECT username, userToFollow FROM followers WHERE username=\'" + user + "\' and userToFollow=\'" + userToRemove + "\';"
    c = db.execute(sql).fetchone()
    user1_sql = "SELECT username FROM users WHERE username=\'" + user  + "\';"
    d = db.execute(user1_sql).fetchall()
    user2_sql = "SELECT username FROM users WHERE username=\'" + userToRemove + "\';"
    e = db.execute(user2_sql).fetchall()
    print(e)
    print(d)
    if not d or not e:
        response.status = 400
        return { 'Status' : response.status, 'message' : 'User does not exist'}
    if not c:
        response.status = 400
        return { 'Status' : response.status, 'message' : 'User was not followed'}
    else:
        execute(db, '''DELETE from followers where username=? and userToFollow=?''', (username, userToRemove))
        response.status = 200
        return { 'Status' : response.status, 'message' : 'Successfully updated.'}
