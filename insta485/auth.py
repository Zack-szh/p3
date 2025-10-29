"""Helpers for authenticating users."""

import hashlib
import flask
import insta485


def authenticate_user(username, password):
    """Verify username and password."""
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT username, password FROM users WHERE username = ?",
        (username,)
    )
    user = cur.fetchone()
    if user is None:
        return None

    stored_hash = user["password"]
    salt, hashed_password = stored_hash.split("$")[1:]
    hash_obj = hashlib.sha512()
    hash_obj.update((salt + password).encode("utf-8"))

    if hash_obj.hexdigest() == hashed_password:
        return user  # Return user info if password matches
    return None


def get_logged_in_username():
    """Return username from session or HTTP Basic Auth."""
    auth = flask.request.authorization
    if 'username' in flask.session:
        return flask.session['username']
    if auth and 'username' in auth and (
        authenticate_user(auth.username, auth.password)
    ):
        return auth.username
    return None
