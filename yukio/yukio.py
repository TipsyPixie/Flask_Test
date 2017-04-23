import os
import sqlite3
from flask import Flask, render_template, session, abort, \
    redirect, flash, request, url_for

DB_FILE = 'db/notice.db'
SCHEMA_FILE = 'db/schema.sql'
CONFIG_FILE = 'YUKIO_CFG'

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(
    {
        'DATABASE': os.path.join(app.root_path, DB_FILE),
        'SECRET_KEY': 'dbb483b5cb12729978799d9d6839a3da1ad0135f07ce81b670cd059d7078c7e2',
        'USERNAME': 'admin',
        'PASSWORD': 'admin'
    }
)
app.debug = True
app.config.from_envvar(CONFIG_FILE, silent=True)


def connect_db():
    connection = sqlite3.connect(app.config['DATABASE'])
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    db = get_db()

    with app.open_resource(SCHEMA_FILE) as schema_file:
        db.cursor().executescript(schema_file.read().decode('iso-8859-1'))
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('database initialized')

def get_db():
    g = app.app_context().g

    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()

    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    g = app.app_context().g

    if hasattr(g, 'sqllite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cursor = db.execute('SELECT title, text FROM entries ORDER BY id DESC')
    entries = cursor.fetchall()

    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('INSERT INTO entries (title, text) VALUES (?, ?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('New entrie was sccuessfully posted')

    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if not request.form['username'] == app.config['USERNAME']:
            error = 'invalid username'
        elif not request.form['password'] == app.config['PASSWORD']:
            error = 'invalid password'
        else:
            session['logged_in'] = True
            flash('successfullly logged in')
            return redirect(url_for('show_entries'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('succesfully logged out')

    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    app.run()
