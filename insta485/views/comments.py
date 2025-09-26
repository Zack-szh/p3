"""Comments."""

import flask
import insta485

LOGGER = flask.logging.create_logger(insta485.app)


@insta485.app.route("/comments/", methods=["POST"])
def update_comments():
    """Comments operations."""
    target = flask.request.args.get("target", "/")

    operation = flask.request.form.get('operation')
    postid = flask.request.form.get('postid')
    commentid = flask.request.form.get('commentid')
    text = flask.request.form.get('text')

    current_user = flask.session.get('username')

    # update database
    connection = insta485.model.get_db()
    if operation == "create":
        # Validate required fields
        if not postid or not text or text.strip() == "":
            flask.abort(400)

        # Insert comment
        connection.execute(
            """
            INSERT INTO comments(owner, postid, text, created)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (current_user, postid, text)
        )

    elif operation == "delete":
        # Delete comment

        cur = connection.execute(
            "SELECT owner FROM comments WHERE commentid=?",
            (commentid,)
        )
        row = cur.fetchone()
        if row is None or row["owner"] != current_user:
            flask.abort(403)

        connection.execute(
            "DELETE FROM comments WHERE commentid=?",
            (commentid,)
        )
    else:
        flask.abort(400)  # Invalid operation

    return flask.redirect(target)
