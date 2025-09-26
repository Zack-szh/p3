"""insta485 likes."""

import flask
import insta485

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/likes/", methods=["POST"])
def update_likes():
    """Handle like and unlike operations for posts."""
    operation = flask.request.form.get('operation')
    postid = flask.request.form.get('postid')
    target = flask.request.args.get("target", "/")

    current_user = flask.session.get('username')
    if not current_user:
        flask.abort(403)  # Must be logged in to like/unlike

    connection = insta485.model.get_db()

    # Check if user already liked this post
    cur = connection.execute(
        "SELECT * FROM likes WHERE owner=? AND postid=?",
        (current_user, postid)
    )
    already_liked = cur.fetchone() is not None

    if operation == 'like':
        if already_liked:
            flask.abort(409)  # conflict
        connection.execute(
            """INSERT INTO likes(owner, postid, created)
            VALUES(?, ?, CURRENT_TIMESTAMP)""",
            (current_user, postid)
        )
    elif operation == 'unlike':
        if not already_liked:
            flask.abort(409)  # conflict
        connection.execute(
            "DELETE FROM likes WHERE owner=? AND postid=?",
            (current_user, postid)
        )
    else:
        flask.abort(400)  # invalid operation

    return flask.redirect(target)
