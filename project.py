# Imports
from flask import Flask, render_template, \
                  url_for, request, redirect,\
                  flash, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import *
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os
import random
import string
import datetime
import json
import httplib2
import requests
# Import login_required from login_decorator.py
from login_decorator import login_req

# Flask instance
app = Flask(__name__)


# GConnect CLIENT_ID

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item-Catalog"


# Connect to database
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine
# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Login - Create anti-forgery state token
@app.route('/login')
def showLogin():
    states = ''.join(random.choice(string.ascii_uppercase +
                                   string.digits) for x in range(32))
    login_session['states'] = states
    return render_template('login.html', STATES=states)


# GConnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Gathers data from Google Sign In API and places
    it inside a session variable.
    """
    # Validate state token
    if request.args.get('states') != login_session['states']:
        responses =
        make_response(json.dumps('Invalid states parameters..'), 401)
        responses.headers['Content-Type'] = 'application/json'
        return responses
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessages'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        responses = make_response(
            json.dumps('Failed to upgrade the authorization code....'), 401)
        responses.headers['Content-Type'] = 'application/json'
        return responses

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response
    h = httplib2.Http()
    responses = h.request(url, 'GET')[1]
    str_responses = responses.decode('utf-8')
    result = json.loads(str_responses)

    # If there was an error in the access token info, abort.
    if result.get('errors') is not None:
        responses = make_response(json.dumps(result.get('errors')), 500)
        responses.headers['Content-Type'] = 'application/json'
        return responses

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['person_id'] != gplus_id:
        responses = make_response(
            json.dumps("Token's person ID doesn't "
                       "match given person ID...."), 401)
        responses.headers['Content-Type'] = 'application/json'
        return responses

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        responses = make_response(
            json.dumps("Token's client ID does not match app's...."), 401)
        responses.headers['Content-Type'] = 'application/json'
        return responses

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        responses = make_response(json.dumps('Current person is'
                                             'already connected....'), 200)
        responses.headers['Content-Type'] = 'application/json'
        return responses

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    personinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(personinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    person_id = getPersonID(login_session['email'])
    if not person_id:
        person_id = createPerson(login_session)
    login_session['person_id'] = person_id

    output = ''
    output += '<h1>Welcomes, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 301px;border-radius: 151px;'
    ' -webkit-border-radius: 151px;-moz-border-radius: 151px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createPerson(login_session):
    newPerson = Person(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newPerson)
    session.commit()
    person =
    session.query(Person).filter_by(email=login_session['email']).one()
    return person.id


def getPersonInfo(person_id):
    person = session.query(Person).filter_by(id=person_id).one()
    return person


def getPersonID(email):
    try:
        person = session.query(Person).filter_by(email=email).one()
        return person.id
    except Exception as e:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        responses = make_response(
            json.dumps('Current person not connected.'), 401)
        responses.headers['Content-Type'] = 'application/json'
        return responses
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    try:
        result['status'] == '200'
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        responses = redirect(url_for('showCatalog'))
        flash("You are now logged out.")
        return responses
    except Exception as error:
        # For whatever reason, the given token was invalid.
        responses = make_response(
            json.dumps('Failed to revoke token for given person.'+error, 400))
        responses.headers['Content-Type'] = 'application/json'
        return responses


# Flask Routing

# Homepage
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    sections = session.query(Section).order_by(asc(Section.name))
    lists = session.query(Lists).order_by(desc(Lists.date)).limit(5)
    return render_template('catalog.html',
                           sections=sections,
                           lists=lists)


# Category Items
@app.route('/catalog/<path:section_name>/lists/')
def showSection(section_name):
    sections = session.query(Section).order_by(asc(Section.name))
    section = session.query(Section).filter_by(name=section_name).one()
    lists = session.query(Lists).filter_by(
            section=section).order_by(asc(Lists.name)).all()
    print(lists)
    count = session.query(Lists).filter_by(section=section).count()
    creator = getPersonInfo(section.person_id)
    if 'username' not in login_session or \
       creator.id != login_session['person_id']:
        return render_template('public_lists.html',
                               section=section.name,
                               sections=sections,
                               lists=lists,
                               count=count)
    else:
        person = getPersonInfo(login_session['person_id'])
        return render_template('lists.html',
                               section=section.name,
                               sections=sections,
                               lists=lists,
                               count=count,
                               person=person)


# Add a category
@app.route('/catalog/addsection', methods=['GET', 'POST'])
# @login_required
def addSection():
    if request.method == 'POST':
        newSection = Section(
            name=request.form['name'],
            person_id=login_session['person_id'])
        print(newSection)
        session.add(newSection)
        session.commit()
        flash('Section Successfully Added!')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('addcategory.html')


# Edit a category
@app.route('/catalog/<path:section_name>/c_edit', methods=['GET', 'POST'])
# @login_required
def editSection(category_name):
    editedSection = session.query(
                                  Section).filter_by(name=category_name).one()
    section = session.query(Section).filter_by(name=category_name).one()
    # See if the logged in user is the owner of item
    creator = getPersonInfo(editedSection.person_id)
    person = getPersonInfo(login_session['person_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Section."
              "This Section belongs to %s" % creator.name)
        return redirect(url_for('showCatalog'))
    # POST methods
    if request.method == 'POST':
        if request.form['name']:
            editedSection.name = request.form['name']
        session.add(editedSection)
        session.commit()
        flash('Section list Successfully Edited!')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editsection.html',
                               sections=editedSection,
                               section=section)


# Delete a category
@app.route('/catalog/<path:section_name>/c_delete', methods=['GET', 'POST'])
# @login_required
def deleteSection(section_name):
    sectionToDelete = session.query(
                       Section).filter_by(name=section_name).one()
    # See if the logged in user is the owner of item
    creator = getPersonInfo(sectionToDelete.person_id)
    person = getPersonInfo(login_session['person_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['person_id']:
        flash("You cannot delete this Section."
              "This Section belongs to %s" % creator.name)
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        session.delete(sectionToDelete)
        session.commit()
        flash('Section Successfully Deleted! '+sectionToDelete.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deletesection.html',
                               section=sectionToDelete)


# Add an item
@app.route('/catalog/add', methods=['GET', 'POST'])
# @login_required
def addList():
    sections = session.query(Section).all()
    if request.method == 'POST':
        newList = Lists(
            name=request.form['name'],
            description=request.form['description'],
            picture=request.form['picture'],
            section=session.query(
                     Section).filter_by(name=request.form['section']).one(),
            date=datetime.datetime.now(),
            person_id=login_session['person_id'])
        session.add(newList)
        session.commit()
        flash('List Successfully Added!')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('addlist.html',
                               sections=sections)


# Edit an item
@app.route('/catalog/<path:section_name>/'
           '<path:list_name>/i_edit', methods=['GET', 'POST'])
# @login_required
def editList(section_name, list_name):
    editedList = session.query(Lists).filter_by(name=list_name).one()
    sections = session.query(Section).all()
    # See if the logged in user is the owner of item
    creator = getPersonInfo(editedList.person_id)
    person = getPersonInfo(login_session['person_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['person_id']:
        flash("You cannot edit this list. "
              "This list belongs to %s" % creator.name)
        return redirect(url_for('showCatalog'))
    # POST methods
    if request.method == 'POST':
        if request.form['name']:
            editedList.name = request.form['name']
        if request.form['description']:
            editedList.description = request.form['description']
        if request.form['picture']:
            editedList.picture = request.form['picture']
        if request.form['section']:
            section = session.query(Section).filter_by(
                       name=request.form['section']).one()
            editedList.section = sectioin
        time = datetime.datetime.now()
        editedList.date = time
        session.add(editedList)
        session.commit()
        flash('Section Item Successfully Edited!')
        return redirect(url_for('showSection',
                                section_name=editedList.section.name))
    else:
        return render_template('editlist.html',
                               list=editedList,
                               sections=sections)


# Delete an item
@app.route('/catalog/<path:section_name>/<path:list_name>/i_delete',
           methods=['GET', 'POST'])
# @login_required
def deleteList(section_name, list_name):
    listToDelete = session.query(Lists).filter_by(name=list_name).one()
    section = session.query(Section).filter_by(name=section_name).one()
    sections = session.query(Section).all()
    # See if the logged in user is the owner of item
    creator = getPersonInfo(listToDelete.person_id)
    person = getPersonInfo(login_session['person_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['person_id']:
        flash("You cannot delete this list. "
              "This list belongs to %s" % creator.name)
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        session.delete(listToDelete)
        session.commit()
        flash('List Successfully Deleted! '+listToDelete.name)
        return redirect(url_for('showSection',
                                section_name=section.name))
    else:
        return render_template('deletelist.html',
                               list=listToDelete)

# JSON


@app.route('/catalog/JSON')
def allListsJSON():
    sections = session.query(Section).all()
    section_dict = [c.serializes for c in sections]
    for c in range(len(section_dict)):
        lists = [i.serializes for i in session.query(
                 Lists).filter_by(section_id=section_dict[c]["id"]).all()]
        if lists:
            section_dict[c]["Item"] = lists
    return jsonify(Section=section_dict)


@app.route('/catalog/sections/JSON')
def sectionsJSON():
    sections = session.query(Section).all()
    return jsonify(sections=[c.serializes for c in sections])


@app.route('/catalog/lists/JSON')
def listsJSON():
    lists = session.query(Lists).all()
    return jsonify(lists=[i.serializes for i in lists])


@app.route('/catalog/<path:section_name>/lists/JSON')
def sectionListsJSON(section_name):
    section = session.query(Section).filter_by(name=section_name).one()
    lists = session.query(Lists).filter_by(section=section).all()
    return jsonify(lists=[i.serializes for i in lists])


@app.route('/catalog/<path:section_name>/<path:list_name>/JSON')
def ListJSON(section_name, list_name):
    section = session.query(Section).filter_by(name=section_name).one()
    list = session.query(Lists).filter_by(
           name=list_name, section=section).one()
    return jsonify(list=[list.serializes])


# Always at end of file !Important!
if __name__ == '__main__':
    app.secret_key = 'APP_SECRET_KEY'
    app.run(host='0.0.0.0', debug=True, port=5000)
