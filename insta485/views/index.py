"""
Insta485 index (main) view.

URLs include:
/
"""
import arrow
import flask
import insta485


@insta485.app.route('/')
def show_index():
    """Display / route."""
    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    logname = flask.session.get('username')
    if logname is None:
        return flask.redirect(flask.url_for('login'))

    cur = connection.execute(
        "SELECT username, fullname "
        "FROM users "
        "WHERE username != ?",
        (logname, )
    )
    users = cur.fetchall()

    posts = []
    post_response = connection.execute(
        """
        SELECT posts.postid, posts.owner, posts.created, posts.filename,
            users.filename AS pfp_url
        FROM posts
        JOIN users ON posts.owner = users.username
        ORDER BY posts.created DESC
        """
    )

    def read_posts():
        # looping through each post
        for row in post_response.fetchall():
            # get comments associated with this post
            comment_response = connection.execute(
                """
                SELECT * FROM comments
                WHERE postid = ?
                ORDER BY postid
                """,
                (row['postid'], )
            )
            comments = comment_response.fetchall()

            # get likes associated with this post
            like_response = connection.execute(
                """
                SELECT * FROM likes
                WHERE postid = ?
                """,
                (row['postid'], )
            )
            likes = like_response.fetchall()
            num_likes = len(likes)

            liked = False
            # whether logname liked the post
            for like in likes:
                if like['owner'] == logname:
                    liked = True

            # process timestamp in human readable format
            timestamp = arrow.get(row['created'])
            timestamp = timestamp.humanize()

            # check whether logname follows row['owner']
            follower_response = connection.execute(
                """
                SELECT followee FROM following
                WHERE follower = ?
                """,
                (logname, )
            ).fetchall()

            followees = [row["followee"] for row in follower_response]

            if row['owner'] in followees or row['owner'] == logname:
                posts.append({
                    "postid": row["postid"],
                    "owner": row["owner"],
                    "created": row["created"],
                    "filename": row["filename"],
                    "pfp_url": row["pfp_url"],
                    "comments": comments,
                    "num_likes": num_likes,
                    "timestamp": timestamp,
                    "liked": liked,
                })

    read_posts()

    # Add database info to context
    context = {"users": users,
               "posts": posts,
               "logname": logname
               }
    return flask.render_template("index.html", **context)
