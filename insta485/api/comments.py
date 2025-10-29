"""REST API for comments."""
import flask
import insta485
from insta485.auth import get_logged_in_username


@insta485.app.route('/api/v1/comments/', methods=['POST'])
def create_comment():
    """Create a new comment for the specified post id."""
    data = flask.request.get_json()

    if data is None or "text" not in data:
        return flask.jsonify(message="missing postid or text"), 400
    postid = flask.request.args.get("postid")
    text = data["text"]

    if not text or text.strip() == "":
        return flask.jsonify(message="empty comment"), 400

    logname = get_logged_in_username()
    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT 1 FROM posts WHERE postid = ?",
        (postid,)
    )
    test_post = cur.fetchone()
    if test_post is None:
        return flask.jsonify(message="postid out of range"), 404

    connection.execute(
        """
        INSERT INTO comments(owner, postid, text, created)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (logname, postid, text)
    )
    cur = connection.execute("SELECT last_insert_rowid() AS lastrowid;")
    commentid = cur.fetchone()["lastrowid"]

    cur = connection.execute(
        """
        SELECT commentid, owner, text FROM comments WHERE commentid = ?
        """, (commentid,)
    )
    row = cur.fetchone()

    response = {
        "commentid": row["commentid"],
        "owner": row["owner"],
        "ownerShowUrl": f"/users/{row['owner']}/",
        "text": row["text"],
        "lognameOwnsThis": True,
        "url": f"/api/v1/comments/{row['commentid']}/",
    }

    return flask.jsonify(**response), 201


@insta485.app.route('/api/v1/comments/<commentid>/', methods=['DELETE'])
def delete_comment(commentid):
    """Delete the comment based on the comment id."""
    logname = get_logged_in_username()
    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT owner FROM comments WHERE commentid = ?",
        (commentid,)
    )
    comment_row = cur.fetchone()
    if comment_row is None:
        return flask.jsonify(message="comment does not exist"), 404

    if comment_row["owner"] != logname:
        return flask.jsonify(message="forbidden"), 403

    connection.execute(
        "DELETE FROM comments WHERE commentid = ?",
        (commentid,)
    )

    return ("", 204)
