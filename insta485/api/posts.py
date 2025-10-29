"""REST API for posts."""
import flask
import insta485
from insta485.auth import authenticate_user, get_logged_in_username


@insta485.app.route('/api/v1/', methods=['GET'])
def get_service():
    """Return API resource URLs as a list of services."""
    services = {}
    for route in insta485.app.url_map.iter_rules():
        if route.rule.startswith("/api/v1/"):
            method = route.rule[len('/api/v1/'):].split('/')
            if method[0]:
                services[method[0]] = f"/api/v1/{method[0]}/"

    # add the base url
    services["url"] = "/api/v1/"

    return flask.jsonify(services)


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/', methods=['GET'])
def get_post(postid_url_slug):
    """Return one post, including comments and likes."""
    connection = insta485.model.get_db()
    cur = connection.execute(
        """
        SELECT * FROM posts WHERE postid = ?
        """,
        (postid_url_slug, )
    )

    post = cur.fetchone()

    # if post does not exist, return 404
    if post is None:
        return flask.jsonify({"message": "Not Found", "status_code": 404}), 404

    # get likes info
    cur = connection.execute(
        "SELECT COUNT(*) AS count FROM likes WHERE postid=?",
        (postid_url_slug,)
    )
    num_likes = cur.fetchone()["count"]

    logname = get_logged_in_username()
    cur = connection.execute(
        "SELECT likeid FROM likes WHERE owner=? AND postid=?",
        (logname, postid_url_slug)
    ) if logname else None
    like = cur.fetchone()
    if like is not None:
        logname_likes_this = True
        like_url = f"/api/v1/likes/{like['likeid']}/"
    else:
        logname_likes_this = False
        like_url = None

    likes = {
        "lognameLikesThis": logname_likes_this,
        "numLikes": num_likes,
        "url": like_url
    }

    cur = connection.execute(
        """
        SELECT commentid, owner, text
        FROM comments
        WHERE postid = ?
        ORDER BY commentid ASC
        """,
        (postid_url_slug,)
    )
    comments = cur.fetchall()

    comment_list = []
    for row in comments:
        comment_list.append({
            "commentid": row["commentid"],
            "lognameOwnsThis": (row["owner"] == logname),
            "owner": row["owner"],
            "ownerShowUrl": f"/users/{row['owner']}/",
            "text": row["text"],
            "url": f"/api/v1/comments/{row['commentid']}/"
        })

    cur = connection.execute(
        """
        SELECT posts.*, users.filename AS owner_img_file
        FROM posts JOIN users ON posts.owner = users.username
        WHERE posts.postid = ?
        """,
        (postid_url_slug, )
    )
    post = cur.fetchone()
    owner_img_url = f"/uploads/{post['owner_img_file']}"

    context = {
        "postid": post['postid'],
        "owner": post['owner'],
        "created": post['created'],
        "likes": likes,
        "comments": comment_list,
        "comments_url": f"/api/v1/comments/?postid={postid_url_slug}",
        "imgUrl": f"/uploads/{post['filename']}",
        "ownerImgUrl": owner_img_url,
        "ownerShowUrl": f"/users/{post['owner']}/",
        "postShowUrl": f"/posts/{postid_url_slug}/",
        "url": flask.request.path,
    }
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/posts/', methods=['GET'])
def get_posts():
    """Return 10 newest post urls and ids, with args and pagination."""
    connection = insta485.model.get_db()

    # AUTHENTIFICATION
    logname = flask.session.get('username')

    if not logname and flask.request.authorization:
        logname = flask.request.authorization['username']
        password = flask.request.authorization['password']

        if authenticate_user(logname, password) is None:
            return flask.jsonify({"message": "Forbidden",
                                  "status_code": 403}), 403
    # redirect to login if noposts session
    if logname is None:
        return flask.jsonify({"message": "Forbidden",
                              "status_code": 403}), 403

    posts = []  # list of dict
    next_url = ''

    # query parameters
    size = flask.request.args.get("size", default=10, type=int)
    page = flask.request.args.get("page", default=0, type=int)
    postid_lte = flask.request.args.get("postid_lte", type=int)

    if size <= 0 or page < 0:
        return flask.jsonify({"message": "Bad requset",
                              "status_code": 400}), 400

    # we need to set a default postid_lte if it is none
    if postid_lte is None:
        # we set it to the current max postid
        cur = connection.execute("SELECT MAX(postid) as maxid FROM posts")
        row = cur.fetchone()
        postid_lte = row['maxid']

    cur = connection.execute(
        """
        SELECT posts.postid
        FROM posts
        LEFT JOIN following
        ON posts.owner = following.followee
        WHERE posts.postid <= ?
        AND (posts.owner = ? OR following.follower = ?)
        GROUP BY posts.postid

        ORDER BY posts.postid DESC
        LIMIT ? OFFSET ?;
        """,
        (postid_lte, logname, logname, size, page * size)
    )

    response = cur.fetchall()

    for post in response:
        posts.append({
            "postid": post['postid'],
            "url": f"/api/v1/posts/{post['postid']}/"
        })

    # build url and next_url
    base_url = "/api/v1/posts/"
    url = base_url
    if flask.request.args:
        url += "?"
        url += "&".join(f"{k}={v}" for k, v in flask.request.args.items())

    if len(posts) == size:
        next_page = page + 1
        next_url = (
            f"{base_url}?size={size}&page={next_page}"
            f"&postid_lte={postid_lte}"
        )
    else:
        next_url = ""

    response = {
        "next": next_url,
        "results": posts,
        "url": url
    }

    return flask.jsonify(**response)
