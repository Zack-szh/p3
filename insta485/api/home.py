"""Home page API."""
import flask
import insta485


@insta485.app.route('/api/v1/')
def get_home():
    """Return the home page."""
    ctx = {
        "comments": "/api/v1/comments/",
        "likes": "/api/v1/likes/",
        "posts": "/api/v1/posts/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**ctx)
