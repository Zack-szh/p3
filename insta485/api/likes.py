"""REST API for likes."""
import flask
import insta485
from insta485.auth import get_logged_in_username


@insta485.app.route('/api/v1/likes/', methods=['POST'])
def get_like():
    """Create a new like for the specified post id."""
    postid = flask.request.args.get("postid", type=int)
    if postid is None:
        return flask.jsonify(message="postid not valid"), 400
    username = get_logged_in_username()
    if username is None:
        return flask.jsonify(message="forbidden"), 403

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT postid FROM posts WHERE postid=?",
        (postid,)
    )
    post = cur.fetchone()
    if post is None:
        return flask.jsonify(message="Post not found"), 404

    cur = connection.execute(
        "SELECT likeid FROM likes WHERE owner=? AND postid=?",
        (username, postid)
    )
    like = cur.fetchone()
    if like is not None:
        # already liked
        alr_liked = {
            "likeid": like["likeid"],
            "url": f"/api/v1/likes/{like['likeid']}/"
        }
        return flask.jsonify(**alr_liked), 200

    connection.execute(
        """
        INSERT INTO likes (owner, postid, created)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """,
        (username, postid)
    )
    cur = connection.execute("SELECT last_insert_rowid() AS likeid")
    likeid = cur.fetchone()['likeid']   # for current like
    new_like = {
        "likeid": likeid,
        "url": f"/api/v1/likes/{likeid}/"
    }
    return flask.jsonify(**new_like), 201


@insta485.app.route('/api/v1/likes/<likeid>/', methods=['DELETE'])
def delete_like(likeid):
    """Delete the like based on the like id."""
    username = get_logged_in_username()
    if username is None:
        return flask.jsonify(message="forbidden"), 403

    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT owner FROM likes WHERE likeid=?",
        (likeid,)
    )
    like = cur.fetchone()
    if like is None:
        return flask.jsonify(message="Like not found"), 404
    if like['owner'] != username:
        return flask.jsonify(message="forbidden"), 403

    connection.execute(
        "DELETE FROM likes WHERE likeid=?",
        (likeid,)
    )

    return ('', 204)
