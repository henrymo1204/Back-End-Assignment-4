import sys
import textwrap
import logging.config
import sqlite3

import bottle
import bottle_sqlite
from bottle import get, post, delete, error, abort, request, response, HTTPResponse

import time


app = bottle.default_app()
app.config.load_config('./etc/timelines.ini')

plugin = bottle_sqlite.Plugin(app.config['sqlite.timelines'])
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
    
    
@post('/posts')
def postTweet(db):
    post = request.json

    if not post:
        abort(400)

    posted_fields = post.keys()
    required_fields = {'username', 'text'}
    
    if not required_fields <= posted_fields:
        abort(400, f'Missing fields: {required_fields - posted_fields}')

    f = '%Y-%m-%d %H:%M:%S'
    now = time.localtime()
    now = time.strftime(f, now)
    
    try:
        post['id'] = execute(db, '''INSERT INTO posts(username, text, time) VALUES (?, ?, ?)''', (post['username'], post['text'], now))

    except sqlite3.IntegrityError as e:
        abort(409, str(e))

    response.status = 201
    post['time'] = now
    return post
    
    
# Returns recent posts from all users that this user follows.    
@get('/followers/<username>/')
def getHomeTimeLine(db, username): 
    posts = query(db, '''SELECT posts.* FROM posts LEFT JOIN followers ON followers.usernameToFollow = posts.username WHERE followers.username = ? ORDER BY posts.time DESC LIMIT 25''', [username])
    if not posts:
    	abort(404)
    	
    return {username: posts}
    
    
# Returns recent posts from all users.
@get('/posts/')
def getPublicTimeLine(db): 
    all_posts = query(db, '''SELECT * FROM posts 
    ORDER BY posts.time DESC 
    LIMIT 25''')
    if not all_posts:
    	abort(404)
    	
    return {'posts': all_posts}
    
    
    
# Returns recent posts from a user.
@get('/posts/<username>')
def getUserTimeLine(db, username):
    user_posts = query(db, '''SELECT * FROM posts 
    WHERE username = ? 
    ORDER BY posts.time DESC 
    LIMIT 25''', [username])
    if not user_posts:
        abort(404)
        
    return {'user': [user_posts]}

