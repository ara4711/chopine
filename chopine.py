#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Requirements: 

En meddelandetjänst, med vilken man kan skicka textmeddelanden till
mottagare och läsa dessa som mottagare. Tjänsten ska stöda fyra
operationer

1. Skicka meddelande till en mottagare, identifierad med epostadress,
telefonnummer eller användarnamn.

2. Hämta nya (sedan förra hämtningen) meddelanden till mottagare

3. Ta bort ett eller flera meddelanden för en mottagare

4. Hämta tidsordnade meddelanden till en mottagare enligt start och stopp index

Implementationen har ett REST-API

Implementationen bygger på
https://www.toptal.com/bottle/building-a-rest-api-with-bottle-framework
http://www.restapitutorial.com/lessons/restquicktips.html

Tester görs med 
   - doctest; enkla tester nära implementationen 
   - webtest; black-box, anropa med uri:er, forms och query-strings etc
     se https://stackoverflow.com/questions/45848418/automated-testing-of-routes-using-python-bottle-framework

TODO use sqlite3 for data storage

TODO user authentication

TODO alternativa test-frameworks att testa
  - hypothesis;  en  QuickCheck klon för python.
    se https://hypothesis.readthedocs.io/en/latest/quickstart.html
  - boddle;  ev som komplement till webtest. Man kan i sitt test 
    populera request structen, och läsa ut response-structen.
    se https://stackoverflow.com/questions/27305449/how-to-unit-test-using-bottle-framework

TODO Add type-annotations using mypy as a checker, or use the coconut-dialect of python


install on macosx:
> sudo easy_install pip
> pip install webtest 

Example message service in python.

Usage::

Start web-server::
    ./chopine.py <port>
Run Tests::
    ./chopine.py

Add a user::
    curl -d "user=pelle&phone=456&email=pelle@uppsala" http://localhost:8080/add_new_user

List users::
    curl http://localhost:8080/users

Dump a user's info::
    curl http://localhost:8080/users/pelle

Add a message::
    curl -d "to=foo&from=ara&msg=hello world." http://localhost:8080/add_msg

Delete some messages::
    curl  http://localhost:8080/msgs/pelle?id=1,3

Fetch messages::
    curl  http://localhost:8080/msgs/pelle
    curl  http://localhost:8080/msgs/pelle?lb=3
    curl  http://localhost:8080/msgs/pelle?lb=2&ub=3

Fetch recent messages::
    curl  http://localhost:8080/msgs/pelle?recent


"""

from bottle import request, response
from bottle import route, post, get, run, template


"""
An example route
"""
@route('/hello/<name>')
def index(name):
    return template('<b>Hello {{name}}</b>!', name=name)



# -------------------------------------------------------------------
# data layer
# abstract away representation
# TODO switch to sqlite3 someday
# import sqlite3
# conn = sqlite3.connect(':memory:')


_users  = dict()                    # the users-database
_msgs   = dict()                    # the messages-database
_msgid  = 0                      # kindof, timestamp

def test_db():
    "for test only!"

    # reset db
    global _msgid
    _users  = dict()                  # the user-database
    _msgs = dict()                    # the message-database
    _msgid     = 0                    # kindof, timestamp

    
    # populate db
    db_addUser('bar','123','a@b')
    db_addUser('ara', '4711-17', 'ara@kth.se')
    db_addUser('foo', '1234-12', 'foo@bar.se')
    db_addMsg('ara', 'foo', 'hello world1')
    db_addMsg('ara', 'foo', 'hello world2')
    db_addMsg('ara', 'foo', 'hello world3')
    db_addMsg('ara', 'foo', 'hello world4')
    

def db_maybeUser(user):
    # TODO cleanup as commented out
    #_users[user] if user in _users.keys() else None
    if user in _users.keys():
        (p,m,c) = _users[user] 
        return (user,p,m,c) 
    else:
        return None        

def db_maybeUserByPhone(phone):
    return next( ((u,p,e,c) for (u,(p,e,c)) in _users.items() if phone == p), None)

def db_maybeUserByEmail(email):
    return next( ((u,p,e,c) for (u,(p,e,c)) in _users.items() if email == e), None)

def db_maybeAnyField(arg):
    """
    lookup via any of  userid, phone, email.
    returns first matching entry

    >>> _users['ara'] = ('123','a@b',0)
    >>> db_maybeAnyField('ara') != None
    True
    >>> db_maybeAnyField('123') != None
    True
    >>> db_maybeAnyField('a@b') != None
    True
    >>> db_maybeAnyField('asdf') != None
    False
    >>> db_maybeAnyField(None) != None
    False
    """
    return next( ((u,p,e,c) for (u,(p,e,c)) in _users.items() if arg in {u,p,e}), None)

def db_addUser(user, phone, email):
    """ 
    >>> db_addUser('bar','123','a@b')
    >>> db_addUser('ara', None, 'ara@kth.se')
    >>> db_addUser('foo', '1234-12', None)
    >>> assert len(_users) == 3
    >>> assert len(_msgs) == 3
    """
    _users[user] = (phone,email,0)
    _msgs[user]  = []               # init the _msgs db. to avoid fussing with None-values later.

def db_updateUser(userdata):
    """ 
    user is assumed to exist already
    >>> _users['ara'] = ('123','a@b',0)
    >>> db_updateUser( ('ara','456','x@y',5) )
    >>> assert _users['ara'] == ('456','x@y',5)
    >>> db_updateUser( ('nosuchuser','456','x@y',5) )  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError
    """
    (u,p,e,c) = userdata
    # inargs validation
    rules = [
        u in _users.keys(),
        type(c) is int
        ]
    if not all(rules):
        raise ValueError('bad in-arg')
    
    _users[u] = (p,e,c)


    
def db_getUsers():
    """
    >>> test_db()
    >>> assert len(db_getUsers()) == 3
    """
    return _users


def db_addMsg(recipient, sender, msg):
    """
    Note: assumes a validated recipient!
    >>> test_db()
    >>> len( _msgs['ara'])
    4
    >>> db_addMsg('ara', 'foo', 'hello world2')
    >>> len( _msgs['ara'])
    5
    >>> len(_msgs['foo']) 
    0
    """
    global _msgid
    _msgs[recipient].append(  (_msgid, sender, msg) )
    _msgid = _msgid+1

def db_getMessages(user):
    """ 
    assumes a validated user!
    >>> test_db()
    >>> assert len(db_getMessages('foo')) == 0
    >>> assert len(db_getMessages('ara')) == 4
    """
    return _msgs[user]

def db_delMsgs(recipient, msgids):
    """ 
    Delete a list of messages for a given user by their id.
    The id's are assumed to be integers!

    >>> test_db()
    >>> len(_msgs['ara'])
    4
    >>> (id0, x, y ) = db_getMessages('ara')[0]
    >>> (id2, x, y ) = db_getMessages('ara')[2]
    >>> (id3, x, y ) = db_getMessages('ara')[3]
    >>> db_delMsgs('ara',[id0,id2,id3]) 
    >>> len(_msgs['ara'])
    1
    """
    _msgs[recipient] = filter(lambda m : not m[0] in msgids,  _msgs[recipient])

    
def db_getMsgIdCount():
    """
    current max index of any message
    """
    global _msgid
    return _msgid

    
# --------------------------------------------------------------------
#  Misc helper functions


def isStrUnsignedInt(str):
    """
    >>> assert isStrUnsignedInt("123")
    >>> assert not isStrUnsignedInt("1a23")
    >>> assert not isStrUnsignedInt("")
    >>> assert not isStrUnsignedInt(None)
    """
    import re
    return re.match(r"\d+$",str or "")


# --------------------------------------------------------------------
#  Web-interface.  routes, input validation and output formatting

# the real webapp, in global scope -- needed by webtest
#  we will also be required to annotate the routes  @app.get(...) etc instead of @get(...) because of this
from bottle import Bottle
app = Bottle()

@app.get('/users')
def get_all_users():

    users  = db_getUsers()
    return {'users': [ {'user': u }  for u in users ] }


@app.get('/users/<user>')
def get_user(user):

    # -- get and validate input data

    mUser = db_maybeUser(user)

    if not mUser:
        # if bad request data, return 400 Bad Request
        response.status = 400
        return

    # -- work 

    (_u, phone,email,_c) = mUser
    return {'user': user, 'phone':phone, 'email':email, 'uri':'/users/'+user}


@app.post('/add_new_user')
def add_new_user():
    f = request.forms

    # -- get and validate input data

    user  = f.get('user')
    phone = f.get('phone')
    email = f.get('email')
    #TODO format validation, and handle missing (optional) fields

    # check for duplicates
    if db_maybeUser(user):
        # if name already exists, return 409 Conflict
        response.status = 409 
        return

    # TODO are duplicate phone numbers allowed?
    
    # -- work
    
    db_addUser(user, phone, email)
    return get_user(user)     # return the newly created user


@app.post('/add_msg')
def add_msg():
    f = request.forms
 
    # -- get and validate input data

    mUser      = db_maybeAnyField(f.get('to'  ))
    recipient  = mUser[0] if mUser else None 

    mUser      = db_maybeAnyField(f.get('from'))
    sender     = mUser[0] if mUser else None
    
    msg        = f.get('msg')                 

    # check valid args
    if None in {recipient, sender, msg}:
        # if bad request data, return 400 Bad Request
        response.status = 400
        return


    # -- work 

    db_addMsg(recipient, sender, msg)
    return 



@app.post('/del_msg')
def del_msg():
    import csv, re

    q = request.query
 
    # -- get and validate input data
    
    [msgids] = csv.reader( [q.id or 'missing_arg!'])
    user  = q.user  # TODO fetch user via authenticated session instead

    rules400 =\
        map( isStrUnsignedInt,  msgids) + [   # msgid syntax
        db_maybeUser(user)                    # valid user
        ]

    if not all(rules400):
        response.status = 400
        return

    # we don't complain if a non-existent msgid is attempted  

    # -- work 
    msgids = map( int, msgids) # cast to int
    db_delMsgs(user, msgids)
    return 





@app.get('/msgs/<user>')  # ?([new]|[lb=<num>][ub=<num>]))
def get_msgs(user):

    q = request.query

    # note:  q.lb returns '' instead of None if a query parameter is missing.
    # I want  '/ara/?lb=' to return 400 and '/ara/?' to return all
    qdk = q.decode().keys()

    # -- get and validate input data
    
    rules400 = [
        # implication, i.e  'a ==> b'  is  'not(a) or (b)'
        not ('lb'  in qdk)   or   isStrUnsignedInt(q.lb), # arg syntax
        not ('ub'  in qdk)   or   isStrUnsignedInt(q.ub), # arg syntax
        not ('new' in qdk)   or   not {'lb','ub'} & set(qdk),  # valid arg combinations
        db_maybeUser(user)                                # valid user
        ]

    if not all(rules400):
        response.status = 400
        return
    
    # -- work

    if 'new' in qdk: #  -- the optional arg 'new'        
        (u,p,e,c) = db_maybeUser(user)         
        lb = c                       # first unseen (by me) message
        ub = db_getMsgIdCount()      # first unused msgid
        db_updateUser( (u,p,e,ub) )  # update user's counter
         
    else:             # -- the optional args 'lb' and 'ub'        
        # missing lb and/or ub  means unlimited range bounds
        from sys import maxint 
        lb = int(q.lb)   if q.lb else 0
        ub = int(q.ub)+1 if q.ub else maxint  # +1 since the user-args are inclusive bounds

        
    # note: messages are time-ordered since they are appended to a list.
    msgs = db_getMessages(user)
    msgs = filter(lambda m : lb <= m[0] < ub, msgs)

    # format output according to reqs
    messages = [ {'id':id, 'from':sender, 'msg':msg}  for (id,sender,msg) in msgs ]
    return {'messages': messages }


def test_doctest():
    import doctest
    doctest.testmod()

def test_webtest():

    from webtest import TestApp

    # wrap the real app in a TestApp object
    ta = TestApp(app)

    # enable printout of exceptions in bottle
    from bottle import debug
    debug(True)


    # WARNING. Since I use åäö in string literals (and comments),
    # python must be instructed to parse the file as utf-8,
    # hence the utf-8 encoding declaration at the top if this file.
    # Note, first used latin-1 but i got webtest confused. It prefers utf-8

    
    # init the example db
    test_db()
    
    #
    # /users
    #
    
    resp = ta.get('/users')
    assert not {'user':'pelle'} in resp.json['users']
    assert {'user':'ara'} in resp.json['users']

    
    #
    # /add_new_user
    #
    
    assert db_maybeUser('pelle') == None
    resp = ta.post('/add_new_user', { 'user':'pelle', 'phone':'456', 'email':'pelle@uppsala'} )
    db_user = db_maybeUser('pelle')
    assert db_user[:3] == ('pelle', '456', 'pelle@uppsala')


    #
    # /add_msg
    #

    # TODO can call to quote be avoided?
    resp = ta.post('/add_msg', {'to':'ara', 'from':'pelle', 'msg':'svanslös!'})
    db_message  = db_getMessages('ara')[-1]
    assert db_message[1:3] == ('pelle', 'svanslös!')

    # test missing fields
    resp = ta.post('/add_msg', {            'from':'pelle', 'msg':'svanslös!'}, status=400)
    resp = ta.post('/add_msg', {'to':'ara',                 'msg':'svanslös!'}, status=400)
    resp = ta.post('/add_msg', {'to':'ara', 'from':'pelle',                  },  status=400)


    #
    # del_msgs
    #
    assert len(_msgs['ara']) == 5
    resp = ta.post('/del_msg?user=ara&id=3')
    assert len(_msgs['ara']) == 4
    resp = ta.post('/del_msg?user=ara&id=1,4')
    assert len(_msgs['ara']) == 2

    resp = ta.post('/del_msg?user=xxx&id=3'     , status=400)  # no such user
    resp = ta.post('/del_msg?user=ara&id=qwe'   , status=400)  # 'id' not an uint
    resp = ta.post('/del_msg?user=ara&id=1,w,4' , status=400)  # 'id' not an uint
    resp = ta.post('/del_msg?id=3'              , status=400)  # missing arg 'user'
    resp = ta.post('/del_msg?user=ara'          , status=400)  # missing arg 'id' 
    resp = ta.post('/del_msg?user=ara&id=4711'  , status=200)  # non-existent 'id' is allowed 

    #
    # /msgs/<user> ([new]|[lb=<num>][ub=<num>]))
    #
    test_db()  # -- re-init
    resp = ta.get('/msgs/ara')
    assert len(resp.json['messages']) == 4

    resp = ta.get('/msgs/ara?lb=1')
    assert len(resp.json['messages']) == 3

    resp = ta.get('/msgs/ara?ub=2')
    assert len(resp.json['messages']) == 3

    resp = ta.get('/msgs/ara?lb=1&ub=2')
    assert len(resp.json['messages']) == 2

    resp = ta.get('/msgs/nousr?ub=2' , status=400)  # no such user
    resp = ta.get('/msgs/ara?lb=qwe' , status=400)  # lb not an uint
    resp = ta.get('/msgs/ara?lb='    , status=400)  # empty lb not an uint
    resp = ta.get('/msgs/ara?ub=qwe' , status=400)  # ub not an uint


    resp = ta.get('/msgs/ara?new')
    assert len(resp.json['messages']) == 4
    resp = ta.post('/add_msg', {'to':'ara', 'from':'pelle', 'msg':'svanslös!'})
    resp = ta.post('/add_msg', {'to':'ara', 'from':'pelle', 'msg':'svanslös!'})
    resp = ta.get('/msgs/ara?new')
    #print resp.json
    assert len(resp.json['messages']) == 2
    resp = ta.get('/msgs/ara?new')
    assert len(resp.json['messages']) == 0
    
    resp = ta.get('/msgs/ara?lb=1&new' , status=400)  # mustn't  mix 'new' and 'lb'/'ub' 
            
if __name__ == "__main__":

    from sys import argv

    # if no args:  run tests
    if len(argv) == 1:
        test_doctest()
        test_webtest()
    

    # start the webserver
    # TODO fancier commandline processing
    if len(argv) == 2:
        # test_db()   # <--- uncomment this if you want some test-entries
        app.run(port=int(argv[1]))
    #else:
    #    app.run(host='localhost', port=8080)


