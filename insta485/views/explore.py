"""
Insta485 explore view.

URLs include:
/
"""
import flask
import insta485


@insta485.app.route('/explore/', methods=['GET'])
def explore():
    """Explore page."""
    logname = flask.session.get('username')
    if logname is None:
        return flask.redirect(flask.url_for('login'))

    # show people who logname is not following
    connection = insta485.model.get_db()

    cur = connection.execute(
        """
        SELECT username, filename
        FROM users
        WHERE username != ?
        AND username NOT IN (
            SELECT followee FROM following WHERE follower = ?
        )
        """,
        (logname, logname)
    )
    not_following = [
        {
            "username": row["username"],
            "user_img_url": "/uploads/" + row["filename"]
        }
        for row in cur.fetchall()
    ]

    return flask.render_template('explore.html',
                                 logname=logname,
                                 not_following=not_following)
