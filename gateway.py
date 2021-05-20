#
# Simple API gateway in Python
#
# Inspired by <https://github.com/vishnuvardhan-kumar/loadbalancer.py>
#

import sys
import json
import http.client
import logging.config

import bottle
from bottle import route, request, response, get, post

import requests
import ast

# Allow JSON values to be loaded from app.config[key]
#
def json_config(key):
    value = app.config[key]
    return json.loads(value)


# Set up app and logging
#
app = bottle.default_app()
app.config.load_config('./etc/gateway.ini')

logging.config.fileConfig(app.config['logging.config'])


# If you want to see traffic being sent from and received by calls to
# the Requests library, add the following to etc/gateway.ini:
#
#   [logging]
#   requests = true
#
if json_config('logging.requests'):
    http.client.HTTPConnection.debuglevel = 1

    requests_log = logging.getLogger('requests.packages.urllib3')
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

    logging.debug('Requests logging enabled')


# Return errors in JSON
#
# Adapted from <https://stackoverflow.com/a/39818780>
#
def json_error_handler(res):
    if res.content_type == 'application/json':
        return res.body
    res.content_type = 'application/json'
    if res.body == 'Unknown Error.':
        res.body = bottle.HTTP_CODES[res.status_code]
    return bottle.json_dumps({'error': res.body})


app.default_error_handler = json_error_handler


# Disable warnings produced by Bottle 0.12.19 when reloader=True
#
# See
#  <https://docs.python.org/3/library/warnings.html#overriding-the-default-filter>
#
if not sys.warnoptions:
    import warnings
    warnings.simplefilter('ignore', ResourceWarning)

@get('/home/<username>')
def getHomeTimeline(username):
    if not authenticated:
        response.status = 401
        return { 'Status' : response.status, 'message' : 'Unauthorized'}
    followers = list(requests.get('http://localhost:5100/followers/' + username).json().values())[0]
    print(followers)
    print(type(followers))
    timeline = list()
    for follower in followers:
         posts = list(requests.get('http://localhost:5200/posts/' + list(follower.values())[0]).json().values())[0][0]
         if posts != 'N':
              for post in posts:
                   timeline.append(post)
    result = sorted(timeline, key=lambda k: k['time'], reverse=True)
    return {'timeline': result}

authenticated = False

@post('/authenticate/<username>/<password>')
def authenticate(username, password):
    global authenticated, user
    payload = {'password' : password}
    url = 'http://localhost:5100/users/' + username + '/password'
    r = requests.post(url, json=payload)
    print(r.status_code)
    if r.status_code == 200:
        authenticated = True
    else:
        authenticated = False
    return { 'Authenticated' : authenticated }


users_server = json_config('proxy.user_streams')
timelines_server = json_config('proxy.timeline_streams')
timelines = timelines_server.copy()

@route('<url:re:.*>', method='ANY')
def gateway(url):
    path = request.urlparts._replace(scheme='', netloc='').geturl()

    if not authenticated:
        response.status = 401
        return { 'Status' : response.status, 'message' : 'Unauthorized'}

    global timelines

    if '/posts' in path:
        if timelines:
             upstream_url = timelines[0] + path
             timelines.pop(0)
             logging.debug('Upstream URL: %s', upstream_url)
             if not timelines:
                  timelines = timelines_server.copy()

    else:
        upstream_url = users_server[0] + path
        logging.debug('Upstream URL: %s', upstream_url)

    headers = {}
    for name, value in request.headers.items():
        if name.casefold() == 'content-length' and not value:
            headers['Content-Length'] = '0'
        else:
            headers[name] = value

    try:
        upstream_response = requests.request(
            request.method,
            upstream_url,
            data=request.body,
            headers=headers,
            cookies=request.cookies,
            stream=True,
        )
    except requests.exceptions.RequestException as e:
        logging.exception(e)
        response.status = 503
        return {
            'method': e.request.method,
            'url': e.request.url,
            'exception': type(e).__name__,
        }

    response.status = upstream_response.status_code
    for name, value in upstream_response.headers.items():
        if name.casefold() == 'transfer-encoding':
            continue
        response.set_header(name, value)
    return upstream_response.content
