"""Insta485 account view."""
import hashlib
import os
import pathlib
import uuid

import flask
import insta485
from insta485.auth import authenticate_user


@insta485.app.route('/accounts/login/', methods=['GET', 'POST'])
def login():
    """Display the login page and handle POST requests for login."""
    if flask.request.method == 'POST':
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')

        # if username or password is empty
        if username is None or password is None:
            return flask.abort(400)

        user = authenticate_user(username, password)

        if user:
            # On success, set session
            flask.session['username'] = username
            flask.flash("Login successful!")
            return flask.redirect(flask.url_for('show_index'))

        flask.flash("Incorrect username or password!")
        flask.abort(403)
        return flask.render_template('login.html')

    return flask.render_template('login.html')


@insta485.app.route('/accounts/logout/', methods=['POST'])
def logout():
    """Log out the user and redirect to login page."""
    flask.session.pop('username', None)  # Remove username from session
    flask.flash("You have successfully logged out!")
    flask.session.clear()
    return flask.redirect(flask.url_for('login'))  # Redirect to login page


@insta485.app.route('/accounts/create/', methods=['GET', 'POST'])
def accounts_create():
    """Create account."""
    logname = flask.session.get('username')
    if logname is not None:
        return flask.redirect(flask.url_for('accounts_edit'))

    return flask.render_template('account_create.html')


@insta485.app.route('/accounts/edit/', methods=['GET'])
def accounts_edit():
    """Edit account."""
    logname = flask.session.get('username')
    if logname is not None:
        connection = insta485.model.get_db()
        cur = connection.execute(
            """SELECT username, fullname, email, filename
            FROM users WHERE username = ?""",
            (logname,)
        )
        user = cur.fetchone()
        ctx = {
            "username": user["username"],
            "fullname": user["fullname"],
            "email": user["email"],
            "pfp": user["filename"]
        }
        return flask.render_template('account_edit.html', **ctx)

    return flask.render_template('account_create.html')


@insta485.app.route('/accounts/delete/', methods=['GET'])
def accounts_delete():
    """Delete account."""
    logname = flask.session.get('username')

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT username FROM users WHERE username = ?",
        (logname,)
    )
    user = cur.fetchone()
    username = user["username"]
    return flask.render_template('account_delete.html', username=username)


@insta485.app.route('/accounts/auth/', methods=['GET'])
def accounts_auth():
    """Account auth."""
    logname = flask.session.get('username')
    if logname is None:
        flask.abort(403)
    return "", 200


@insta485.app.route('/accounts/password/', methods=['GET'])
def accounts_password():
    """Account password."""
    logname = flask.session.get('username')

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT username FROM users WHERE username = ?",
        (logname,)
    )
    user = cur.fetchone()
    username = user["username"]
    return flask.render_template('account_password.html', username=username)


LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route('/accounts/', methods=['POST'])
def accounts():
    """Perform account operations based on POST form content."""
    operation = flask.request.form.get('operation')
    logname = flask.session.get('username')
    target = flask.request.args.get('target', '/')
    connection = insta485.model.get_db()

    if operation == "login":
        return do_login(connection, target)

    if operation == "create":
        return do_create(connection, target)

    if operation == "delete":
        return do_delete(logname, connection, target)

    if operation == "edit_account":
        return do_edit_account(logname, connection, target)

    if operation == "update_password":
        return do_update_password(logname, connection, target)

    # else Unknown operation
    flask.abort(400)


def do_login(connection, target):
    """Login."""
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    if not username or not password:
        flask.abort(400)

    cur = connection.execute(
        "SELECT username, password FROM users WHERE username = ?",
        (username,)
    )
    u = cur.fetchone()
    if u is None:
        flask.abort(403)

    stored_hash = u['password']
    try:
        algorithm, salt, hashed_password = stored_hash.split('$')
    except ValueError:
        flask.abort(500)

    hash_obj = hashlib.new(algorithm)
    hash_obj.update((salt + password).encode('utf-8'))
    if hash_obj.hexdigest() != hashed_password:
        flask.abort(403)

    flask.session['username'] = username
    return flask.redirect(target)


def do_create(connection, target):
    """Create account."""
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    fullname = flask.request.form.get('fullname')
    email = flask.request.form.get('email')
    fileobj = flask.request.files.get('file')

    if not all([username, password, fullname, email, fileobj]):
        flask.abort(400)

    cur = connection.execute(
        "SELECT username FROM users WHERE username = ?",
        (username,)
    )
    if cur.fetchone():
        flask.abort(409)

    filename = fileobj.filename
    suffix = pathlib.Path(filename).suffix.lower()
    uuid_basename = f"{uuid.uuid4().hex}{suffix}"
    path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
    fileobj.save(path)

    salt = uuid.uuid4().hex
    hash_obj = hashlib.new('sha512')
    hash_obj.update((salt + password).encode('utf-8'))
    password_db_string = f"{'sha512'}${salt}${hash_obj.hexdigest()}"

    connection.execute(
        """INSERT INTO
        users(username, fullname, email, filename, password)
        VALUES (?, ?, ?, ?, ?)""",
        (username, fullname, email, uuid_basename, password_db_string)
    )

    flask.session['username'] = username
    return flask.redirect(target)


def do_delete(logname, connection, target):
    """Delete account."""
    if not logname:
        return flask.redirect('/accounts/login/')

    cur = connection.execute(
        "SELECT filename FROM posts WHERE owner = ?",
        (logname,)
    )
    for row in cur.fetchall():
        post_path = insta485.app.config["UPLOAD_FOLDER"] / row['filename']
        if post_path.exists():
            os.remove(post_path)

    cur = connection.execute(
        "SELECT filename FROM users WHERE username = ?",
        (logname,)
    )
    row = cur.fetchone()
    if row:
        icon_path = insta485.app.config["UPLOAD_FOLDER"] / row['filename']
        if icon_path.exists():
            os.remove(icon_path)

    connection.execute("DELETE FROM users WHERE username = ?", (logname,))
    flask.session.clear()
    return flask.redirect(target)


def do_edit_account(logname, connection, target):
    """Edit account."""
    if not logname:
        flask.abort(403)

    fullname = flask.request.form.get('fullname')
    email = flask.request.form.get('email')
    fileobj = flask.request.files.get('file')

    if not fullname or not email:
        flask.abort(400)

    if fileobj and fileobj.filename != "":
        # Save new icon
        filename = fileobj.filename
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
        fileobj.save(path)

        # Delete old icon
        cur = connection.execute(
            "SELECT filename FROM users WHERE username = ?",
            (logname,)
        )
        row = cur.fetchone()
        if row:
            old_path = (
                insta485.app.config["UPLOAD_FOLDER"] /
                row["filename"]
            )
            if old_path.exists():
                os.remove(old_path)

        connection.execute(
            """UPDATE users SET fullname = ?, email = ?,
            filename = ? WHERE username = ?""",
            (fullname, email, uuid_basename, logname)
        )
    else:
        connection.execute(
            "UPDATE users SET fullname = ?, email = ? WHERE username = ?",
            (fullname, email, logname)
        )

    return flask.redirect(target)


def do_update_password(logname, connection, target):
    """Update password."""
    if not logname:
        flask.abort(403)

    password = flask.request.form.get('password')
    new_password1 = flask.request.form.get('new_password1')
    new_password2 = flask.request.form.get('new_password2')

    if not all([password, new_password1, new_password2]):
        flask.abort(400)

    cur = connection.execute(
        "SELECT password FROM users WHERE username = ?",
        (logname,)
    )
    row = cur.fetchone()
    if not row:
        flask.abort(403)

    stored_hash = row['password']
    algorithm, salt, hashed_password = stored_hash.split('$')
    hash_obj = hashlib.new(algorithm)
    hash_obj.update((salt + password).encode('utf-8'))
    if hash_obj.hexdigest() != hashed_password:
        flask.abort(403)

    if new_password1 != new_password2:
        flask.abort(401)

    new_salt = uuid.uuid4().hex
    hash_obj = hashlib.new(algorithm)
    hash_obj.update((new_salt + new_password1).encode('utf-8'))
    password_db_string = f"{algorithm}${new_salt}${hash_obj.hexdigest()}"
    connection.execute(
        "UPDATE users SET password = ? WHERE username = ?",
        (password_db_string, logname)
    )

    return flask.redirect(target)
