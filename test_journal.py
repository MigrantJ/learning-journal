# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

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
def app():
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


def test_write_entry(db_session):
    kwargs = {'title': "Test Title", 'text': "Test entry text"}
    kwargs['session'] = db_session
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


def test_empty_listing(app):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No entries here so far'
    assert expected in actual


def test_listing(app, test_entry):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    for field in ['title', 'text']:
        expected = getattr(test_entry, field, 'none')
        assert expected in actual


def test_post_to_add_view(app):
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post',
        }
    response = app.post('/add', params=entry_data, status='3*')
    redirected = response.follow()
    actual = redirected.body
    for expected in entry_data.values():
        assert expected in actual


def test_get_to_add_view(app):
    entry_data = {
        'title': 'test',
        'text': 'text'
    }
    response = app.get('/add', params=entry_data, status='404 Not Found')
    assert response.status_code == 404


def test_add_view_no_params(app):
    response = app.post('/add', params={}, status='5*')
    assert response.status_code == 500
    assert 'IntegrityError' in response.body