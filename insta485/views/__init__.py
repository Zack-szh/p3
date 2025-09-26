"""Views, one for each Insta485 page."""
from flask import Flask
import insta485.config
from insta485.views.index import show_index
from insta485.views.uploads import uploaded_file
from insta485.views.users import show_user_profile
from insta485.views.likes import update_likes
from insta485.views.users import show_following
from insta485.views.comments import update_comments
from insta485.views.account import login
from insta485.views.explore import explore
from insta485.views.posts import posts
from insta485.views.account import accounts_edit
