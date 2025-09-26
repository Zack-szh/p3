"""
Insta485 uploads.

URLs include:
/
"""
import flask
import insta485


@insta485.app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Upload file."""
    if not flask.session.get('username'):
        flask.abort(403)
    return flask.send_from_directory(insta485.config.UPLOAD_FOLDER, filename)
