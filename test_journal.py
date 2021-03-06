# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from pyramid import testing
from cryptacular.bcrypt import BCRYPTPasswordManager

TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://jimgrant@localhost:5432/test-learning-journal'
)
os.environ['DATABASE_URL'] = TEST_DATABASE_URL
os.environ['TESTING'] = 'True'

import journal

@pytest.fixture(scope='session')
def connection(request):
    engine = create_engine(TEST_DATABASE_URL)
    journal.Base.metadata.create_all(engine)
    connection = engine.connect()
    journal.DBSession.registry.clear()
    journal.DBSession.configure(bind=connection)
    journal.Base.metadata.bind = engine
    request.addfinalizer(journal.Base.metadata.drop_all)
    return connection

@pytest.fixture()
def db_session(request, connection):
    from transaction import abort
    trans = connection.begin()
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)

    from journal import DBSession
    return DBSession

@pytest.fixture()
def app(db_session):
    from journal import main
    from webtest import TestApp
    testapp = TestApp(main())
    return testapp

@pytest.fixture()
def test_entry(db_session):
    from journal import Entry
    entry = Entry.write(title="Test", text="Test Text", session=db_session)
    db_session.flush()
    return entry

@pytest.fixture(scope='function')
def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'admin',
        'auth.password': manager.encode('secret'),
        }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req


def test_write_entry(db_session):
    kwargs = {'title': "Test Title", 'text': "Test entry text",
              'session': db_session}
    # first, assert that there are no entries in the database:
    assert db_session.query(journal.Entry).count() == 0
    # now, create an entry using the 'write' class method
    entry = journal.Entry.write(**kwargs)

    # the entry we get back ought to be an instance of Entry
    assert isinstance(entry, journal.Entry)
    # id and created are generated automatically, but only on writing to
    # the database
    auto_fields = ['id', 'created']
    for field in auto_fields:
        assert getattr(entry, field, None) is None

    # flush the session to "write" the data to the database
    db_session.flush()
    # now, we should have one entry:
    assert db_session.query(journal.Entry).count() == 1
    for field in kwargs:
        if field != 'session':
            assert getattr(entry, field, '') == kwargs[field]
    # id and created should be set automatically upon writing to db:
    for auto in ['id', 'created']:
        assert getattr(entry, auto, None) is not None


def test_write_entry_no_title(db_session):
    # we must provide a title when writing an entry
    kwargs = {'text': 'There is no title'}
    entry = journal.Entry.write(**kwargs)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_write_entry_no_text(db_session):
    # we must provide a title when writing an entry
    kwargs = {'title': 'There is no text'}
    entry = journal.Entry.write(**kwargs)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_read_entries_empty(db_session):
    entries = journal.Entry.all()
    assert len(entries) == 0


def test_read_entries_one(db_session):
    title_template = "Title {}"
    text_template = "Entry Text {}"
    # write three entries, with order clear in the title and text
    for x in range(3):
        journal.Entry.write(
            title=title_template.format(x),
            text=text_template.format(x),
            session=db_session)
        db_session.flush()
    entries = journal.Entry.all()
    assert len(entries) == 3
    assert entries[0].title > entries[1].title > entries[2].title
    for entry in entries:
        assert isinstance(entry, journal.Entry)


def test_one_entry(db_session, test_entry):
    eid = test_entry.id
    entry = journal.Entry.one(eid)
    assert isinstance(entry, journal.Entry)
    assert entry.title == test_entry.title


def test_empty_listing(app):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No entries here so far'
    assert expected in actual


def test_listing(app, test_entry):
    response = app.get('/detail/' + unicode(test_entry.id))
    assert response.status_code == 200
    actual = response.body
    for field in ['title', 'text']:
        expected = getattr(test_entry, field, 'none')
        assert expected in actual


LOGIN_FORM = '<form id="login-form"'


def test_post_to_add_view_no_auth(app):
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post',
        }
    response = app.post('/add', params=entry_data, status='3*')
    redirected = response.follow()
    actual = redirected.body
    assert LOGIN_FORM in actual


def test_post_to_add_view(app):
    test_login_success(app)
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post',
        }
    response = app.post('/add', params=entry_data, status='3*')
    redirected = response.follow()
    actual = redirected.body
    assert entry_data['title'] in actual


def test_add_view_no_params(app):
    test_login_success(app)
    response = app.post('/add', params={}, status='5*')
    assert response.status_code == 500
    assert 'IntegrityError' in response.body


def test_post_edit_view_no_auth(app, test_entry):
    entry_data = {
        'title': 'Modify Test',
        'text': 'This is a post that has been edited'
    }
    response = app.post(
        '/edit/' + unicode(test_entry.id),
        params=entry_data,
        status='3*'
    )
    redirected = response.follow()
    actual = redirected.body
    assert LOGIN_FORM in actual


def test_post_edit_view(app, test_entry):
    test_login_success(app)
    entry_data = {
        'title': 'Modify Test',
        'text': 'This is a post that has been edited'
    }
    response = app.post(
        '/edit/' + unicode(test_entry.id),
        params=entry_data,
        status='3*'
    )
    redirected = response.follow()
    actual = redirected.body
    assert entry_data['title'] in actual


def test_edit_view_no_params(app, test_entry):
    test_login_success(app)
    response = app.post(
        '/edit/' + unicode(test_entry.id),
        params={},
        status='4*'
    )
    assert response.status_code == 400
    assert 'Bad Request' in response.body


def test_do_login_success(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'admin', 'password': 'secret'}
    assert do_login(auth_req)


def test_do_login_bad_pass(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'admin', 'password': 'wrong'}
    assert not do_login(auth_req)


def test_do_login_bad_user(auth_req):
    from journal import do_login
    auth_req.params = {'username': 'bad', 'password': 'secret'}
    assert not do_login(auth_req)


def test_do_login_missing_params(auth_req):
    from journal import do_login
    for params in ({'username': 'admin'}, {'password': 'secret'}):
        auth_req.params = params
        with pytest.raises(ValueError):
            do_login(auth_req)

DIV_CREATE_NEW = '<div class="create-new">'


def login_helper(username, password, app):
    """encapsulate app login for reuse in tests

    Accept all status codes so that we can make assertions in tests
    """
    login_data = {'username': username, 'password': password}
    return app.post('/login', params=login_data, status='*')


def test_start_as_anonymous(app):
    response = app.get('/', status=200)
    actual = response.body
    assert DIV_CREATE_NEW not in actual


def test_login_success(app):
    username, password = ('admin', 'secret')
    redirect = login_helper(username, password, app)
    assert redirect.status_code == 302
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    assert DIV_CREATE_NEW in actual


def test_login_fails(app):
    username, password = ('admin', 'wrong')
    response = login_helper(username, password, app)
    assert response.status_code == 200
    actual = response.body
    assert "Login Failed" in actual
    assert DIV_CREATE_NEW not in actual


def test_logout(app):
    # re-use existing code to ensure we are logged in when we begin
    test_login_success(app)
    redirect = app.get('/logout', status="3*")
    response = redirect.follow()
    assert response.status_code == 200
    actual = response.body
    assert DIV_CREATE_NEW not in actual


def test_add_view_no_auth(app):
    response = app.get('/add')
    assert response.status_code == 302
    response = response.follow()
    assert response.status_code == 200
    actual = response.body
    assert LOGIN_FORM in actual


def test_add_view(app):
    test_login_success(app)
    response = app.get('/add')
    assert response.status_code == 200
    form = response.form
    test_data = {'title': 'Create Test', 'text': 'Create Test Text'}
    for field in test_data.keys():
        assert field in form.fields.keys()
        form[field] = test_data[field]

    submit_res = form.submit()
    assert submit_res.status_code == 302
    response = submit_res.follow()
    assert response.status_code == 200
    assert test_data['title'] in response.body


def test_edit_view_no_auth(app, test_entry):
    response = app.get('/edit/' + unicode(test_entry.id))
    assert response.status_code == 302
    response = response.follow()
    assert response.status_code == 200
    actual = response.body
    assert LOGIN_FORM in actual


def test_edit_view(app, test_entry):
    test_login_success(app)
    url = '/edit/' + unicode(test_entry.id)
    response = app.get(url)
    assert response.status_code == 200
    form = response.form
    test_data = {'title': 'Edit Test', 'text': 'Edit Test Text'}
    for field in test_data.keys():
        assert field in form.fields.keys()
        assert form[field].value == getattr(test_entry, field)
        form[field] = test_data[field]

    submit_res = form.submit()
    assert submit_res.status_code == 302
    response = submit_res.follow()
    assert response.status_code == 200
    assert test_data['title'] in response.body
