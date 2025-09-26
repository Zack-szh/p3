"""Insta485 user view."""
import flask
import insta485


@insta485.app.route('/users/<user_url_slug>/')
def show_user_profile(user_url_slug):
    """Display / route."""
    # Connect to database
    connection = insta485.model.get_db()

    # info abt current user
    # current_user = flask.session.get('username')
    current_user = flask.session.get('username')
    if current_user is None:
        return flask.redirect('/accounts/login/')

    cur = connection.execute(
        "SELECT username, fullname FROM users WHERE username =?",
        (user_url_slug,)
    )
    user = cur.fetchone()
    if user is None:
        flask.abort(404)
    username = user["username"]
    fullname = user["fullname"]

    if current_user is not None and current_user != user_url_slug:
        cur = connection.execute(
            "SELECT 1 FROM following WHERE followee=? AND follower=?",
            (user_url_slug, current_user)
        )
        relationship = cur.fetchone() is not None
    else:
        relationship = None

    cur = connection.execute(
        "SELECT COUNT(*) AS followers FROM following WHERE followee=?",
        (user_url_slug,)
    )
    num_followers = cur.fetchone()["followers"]

    cur = connection.execute(
        "SELECT COUNT(*) AS count FROM following WHERE follower=?",
        (user_url_slug,)
    )
    num_following = cur.fetchone()["count"]

    cur = connection.execute(
        "SELECT COUNT(*) AS total_posts FROM posts WHERE owner=?",
        (user_url_slug,)
    )
    total_posts = cur.fetchone()["total_posts"]

    cur = connection.execute(
        """SELECT postid, filename FROM posts WHERE owner=?
        ORDER BY postid DESC""",
        (user_url_slug,)
    )
    posts = [
        {
            "postid": row["postid"],
            "img_url": "/uploads/" + row["filename"]
        }
        for row in cur.fetchall()
    ]

    return flask.render_template(
        "user.html",
        logname=current_user,
        username=username,
        fullname=fullname,
        followers=num_followers,
        following=num_following,
        total_posts=total_posts,
        posts=posts,
        logname_follows_username=relationship,
    )


@insta485.app.route('/users/<user_url_slug>/following/')
def show_following(user_url_slug):
    """Show following list."""
    connection = insta485.model.get_db()

    current_user = flask.session.get('username')
    if current_user is None:
        return flask.redirect('/accounts/login/')

    cur = connection.execute(
        "SELECT username FROM users WHERE username =?",
        (user_url_slug,)
    )
    user = cur.fetchone()
    if user is None:
        flask.abort(404)

    cur = connection.execute(
        """
        SELECT u.username, u.filename
        FROM following AS f
        JOIN users AS u ON f.followee = u.username
        WHERE f.follower = ?
        """,
        (user_url_slug, )
    )
    following = [
        {
            "username": row["username"],
            "user_img_url": "/uploads/" + row["filename"],
            "logname_follows_username": True
        }
        for row in cur.fetchall()
    ]
    return flask.render_template(
        "following.html",
        logname=current_user,
        following=following
    )


@insta485.app.route('/users/<user_url_slug>/followers/')
def show_followers(user_url_slug):
    """Show follower list."""
    connection = insta485.model.get_db()

    current_user = flask.session.get('username')
    if current_user is None:
        return flask.redirect('/accounts/login/')

    cur = connection.execute(
        "SELECT username, fullname FROM users WHERE username =?",
        (user_url_slug,)
    )
    user = cur.fetchone()
    if user is None:
        flask.abort(404)

    cur = connection.execute(
        """
        SELECT u.username, u.filename
        FROM following AS f
        JOIN users AS u ON f.follower = u.username
        WHERE f.followee = ?
        """,
        (user_url_slug, )
    )
    followers = []
    for row in cur.fetchall():
        follower_username = row["username"]
        cur2 = connection.execute(
            "SELECT 1 FROM following WHERE follower = ? AND followee = ?",
            (current_user, follower_username)
        )
        is_following = cur2.fetchone() is not None
        followers.append({
            "username": follower_username,
            "user_img_url": "/uploads/" + row["filename"],
            "logname_follows_username": is_following
        })
    return flask.render_template(
        "followers.html",
        logname=current_user,
        followers=followers
    )


@insta485.app.route('/following/', methods=["POST"])
def follow_action():
    """Follow/unfollow functionality."""
    logname = flask.session.get('username')
    operation = flask.request.form["operation"]
    username = flask.request.form["username"]
    target = flask.request.args.get("target")
    connection = insta485.model.get_db()

    # is logname following username?
    cur = connection.execute(
        "SELECT * FROM following WHERE follower=? AND followee=?",
        (logname, username)
    )

    if operation == "follow":
        if cur.fetchone() is not None:
            flask.abort(409)
        connection.execute(
            "INSERT INTO following(follower, followee) VALUES (?, ?)",
            (logname, username)
        )
    elif operation == "unfollow":
        if cur.fetchone() is None:
            flask.abort(409)
        connection.execute(
            "DELETE FROM following WHERE follower=? AND followee=?",
            (logname, username)
        )
    else:
        flask.abort(400)

    return flask.redirect(target)
