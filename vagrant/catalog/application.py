from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from db_setup import Base, Category, Item, User

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# My helper functions
def catName(cat_id):
    cat = session.query(Category).filter_by(id=cat_id).one()
    return cat.name


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        # response = make_response(json.dumps('Successfully disconnected.'), 200)
        # response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showLatest'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/item/<string:item_name>/JSON')
def itemJSON(item_name):
    """JSON API for a given item"""
    item = session.query(Item).filter_by(name=item_name).one()
    return jsonify(item=item.serialize)


@app.route('/')
@app.route('/catalog/')
def showLatest():
    """The main page, showing the latest items added"""
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(10)
    title = "Latest items"
    if 'username' not in login_session:
        return render_template('publicshowitems.html', categories=categories, items=items, title=title, latest=True, catName=catName)
    else:
        return render_template('showitems.html', categories=categories, items=items, title=title, latest=True, catName=catName)


@app.route('/catalog/category/<string:category_name>/')
def showCategory(category_name):
    """The page displaying the items from a specific category"""
    categories = session.query(Category.name).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item.name).filter_by(category_id=category.id)
    title = category_name
    if 'username' not in login_session:
        return render_template('publicshowitems.html', categories=categories, items=items, title=title)
    else:
        return render_template('showitems.html', categories=categories, items=items, title=title)


@app.route('/catalog/new/', methods=['GET', 'POST'])
def newItem():
    """The form used to add a new item"""
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category']

        if not (category_id):
            error = "Make sure the item is within a category!"
            flash(error)
            return render_template('newitem.html', categories=categories, name=name, description=description)

        try:
            existent = session.query(Item).filter_by(name=name).one()
        except:
            existent = None
        if existent:
            error = "There is already one item with the same name!"
            flash(error)
            return render_template('newitem.html', categories=categories, name=name, description=description)

        newItem = Item(name=name, description=description, category_id=category_id, user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("Item successfuly added!")
        category_name = catName(category_id)
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('newitem.html', categories=categories)


@app.route('/catalog/item/<string:item_name>/')
def showItem(item_name):
    """The page displaying a specific item"""
    item = session.query(Item).filter_by(name=item_name).one()
    if 'username' not in login_session or item.user_id != login_session['user_id']:
        return render_template('publicitem.html', item=item)
    else:
        return render_template('item.html', item=item)


@app.route('/catalog/item/<string:item_name>/edit/', methods=['GET', 'POST'])
def editItem(item_name):
    """The form used to edit an item"""
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(name=item_name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = request.form['category']

        try:
            existent = session.query(Item).filter_by(name=name).one()
        except:
            existent = None
        if existent and not name == item.name:
            error = "There is already one item with the same name!"
            flash(error)
            return render_template('edititem.html', categories=categories, item=item)

        item.name = name
        item.description = description
        item.category_id = category_id
        session.add(item)
        session.commit()
        flash("Item successfully edited!")
        category_name = catName(category_id)
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('edititem.html', categories=categories, item=item)


@app.route('/catalog/item/<string:item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(item_name):
    """The form used to delete an item"""
    item = session.query(Item).filter_by(name=item_name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        category_name = catName(item.category_id)
        session.delete(item)
        session.commit()
        flash("Item successfuly deleted!")
        return redirect(url_for('showCategory', category_name=category_name))
    else:
        return render_template('deleteitem.html', item=item)


if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)