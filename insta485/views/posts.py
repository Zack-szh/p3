"""posts."""

import os
import uuid

import flask

import insta485


@insta485.app.route('/posts/<postid_url_slug>/', methods=["GET"])
def posts(postid_url_slug):
    """Display a single post page with comments and likes."""
    current_user = flask.session.get('username')
    if current_user is None:
        return flask.redirect(flask.url_for('login'))

    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT * FROM posts WHERE postid=?",
        (postid_url_slug,)
    )
    post = cur.fetchone()
    if post is None:
        flask.abort(404)

    cur = connection.execute(
        "SELECT * FROM comments WHERE postid=? ORDER BY commentid ASC",
        (postid_url_slug,)
    )
    comments = cur.fetchall()

    cur = connection.execute(
        "SELECT * FROM likes WHERE postid=?",
        (postid_url_slug,)
    )
    likes = cur.fetchall()
    num_likes = len(likes)

    # Determine if current user has liked this post
    liked = any(like['owner'] == current_user for like in likes)

    # Fetch post owner info
    cur = connection.execute(
        "SELECT * FROM users WHERE username=?",
        (post["owner"],)
    )
    owner = cur.fetchone()

    ctx = {
        "logname": current_user,
        "owner": post["owner"],
        "timestamp": post["created"],
        "likes": num_likes,
        "comments": comments,
        "post": post,
        "img_url": flask.url_for("uploaded_file", filename=post["filename"]),
        "owner_img_url": flask.url_for(
            "uploaded_file",
            filename=owner["filename"]
        ),
        "liked": liked,
    }

    return flask.render_template("post.html", **ctx)


@insta485.app.route("/posts/", methods=["POST"])
def handle_posts():
    """Post ops."""
    operation = flask.request.form.get("operation")

    if operation == "create":
        # upload new post
        fileobj = flask.request.files["file"]
        filename = str(uuid.uuid4()) + os.path.splitext(fileobj.filename)[1]
        file_path = os.path.join(insta485.app.config["UPLOAD_FOLDER"],
                                 filename)
        fileobj.save(file_path)

        connection = insta485.model.get_db()
        connection.execute(
            "INSERT INTO posts (filename, owner) VALUES (?, ?)",
            (filename, flask.session["username"])
        )
        return flask.redirect("/users/" + flask.session["username"] + "/")

    if operation == "delete":
        postid = flask.request.form["postid"]

        connection = insta485.model.get_db()
        cur = connection.execute(
            "SELECT filename FROM posts WHERE postid=?",
            (postid,)
        )
        post = cur.fetchone()

        if post is None:
            flask.abort(404)

        # delete from DB
        connection.execute(
            "DELETE FROM posts WHERE postid=?",
            (postid,)
        )
        # delete file from disk
        os.remove(os.path.join(insta485.app.config["UPLOAD_FOLDER"],
                               post["filename"]))

        return flask.redirect("/users/" + flask.session["username"] + "/")

    flask.abort(400)
