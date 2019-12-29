from urllib.parse import urlparse
import mistletoe
from sqlalchemy import func
from bs4 import BeautifulSoup

from ruqqus.helpers.wrappers import *
from ruqqus.helpers.base36 import *
from ruqqus.helpers.sanitize import *
from ruqqus.helpers.filters import *
from ruqqus.helpers.embed import *
from ruqqus.helpers.markdown import *
from ruqqus.helpers.get import *
from ruqqus.classes import *
from flask import *
from ruqqus.__main__ import app, db, cache

BAN_REASONS=['',
            "URL shorteners are not permitted."
            ]

@app.route("/api/is_available/<name>", methods=["GET"])
def api_is_available(name):
    if db.query(User.username).filter(User.username.ilike(name)).count():
        return jsonify({name:False})
    else:
        return jsonify({name:True})

@app.route("/uid/<uid>", methods=["GET"])
@admin_level_required(1)
def user_uid(uid, v):

    user=db.query(User).filter_by(id=base36decode(uid)).first()
    if user:
        return redirect(user.permalink)
    else:
        abort(404)

@app.route("/u/<username>", methods=["GET"])
@app.route("/u/<username>/posts", methods=["GET"])
@app.route("/@<username>", methods=["GET"])
@auth_desired
def u_username(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    result = db.query(User).filter(User.username.ilike(username)).first()

    if not result:
        abort(404)

    #check for wrong cases

    if username != result.username:
        return redirect(result.url)
        
    return result.rendered_userpage(v=v)

@app.route("/u/<username>/comments", methods=["GET"])
@app.route("/@<username>/comments", methods=["GET"])
@auth_desired
def u_username_comments(username, v=None):
    
    #username is unique so at most this returns one result. Otherwise 404
    
    #case insensitive search

    result = db.query(User).filter(User.username.ilike(username)).first()

    if not result:
        abort(404)

    #check for wrong cases

    if username != result.username:
        return redirect(result.url)
        
    return result.rendered_comments_page(v=v)

@app.route("/api/follow/<username>", methods=["POST"])
@auth_required
def follow_user(username, v):

    target=get_user(username)

    #check for existing follow
    if db.query(Follow).filter_by(user_id=v.id, target_id=target.id).first():
        abort(409)

    new_follow=Follow(user_id=v.id,
                      target_id=target.id)

    db.add(new_follow)
    db.commit()

    cache.delete_memoized(User.idlist, v, kind="user")

    return "", 204


@app.route("/api/unfollow/<username>", methods=["POST"])
@auth_required
def unfollow_user(username, v):

    target=get_user(username)

    #check for existing follow
    follow= db.query(Follow).filter_by(user_id=v.id, target_id=target.id).first()

    if not follow:
        abort(409)

    db.delete(follow)
    db.commit()

    cache.delete_memoized(User.idlist, v, kind="user")

    return "", 204

@app.route("/settings/images/profile", methods=["POST"])
@auth_required
@validate_formkey
def settings_images_profile(v):

    v.set_profile(request.files["profile"])

    return render_template("settings_profile.html", v=v, msg="Profile successfully updated.")

@app.route("/settings/images/banner", methods=["POST"])
@auth_required
@validate_formkey
def settings_images_banner(v):

    v.set_banner(request.files["banner"])

    return render_template("settings_profile.html", v=v, msg="Banner successfully updated.")
