import json
import os
from hashter import db
from flask import current_app, render_template, request, Blueprint
from hashter.models import Post, User
from flask_login import current_user, login_required
from flask_socketio import send, emit
from hashter.users.utils import delete_temp_image



main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
	if current_user.is_authenticated:
		tribe = current_user.tribe
		page = request.args.get('page', 1, type=int)
		posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=20)
		if current_user.temp_image:
			delete_temp_image()
		return render_template('home.html', posts=posts, tribe=tribe)
	else:
		return render_template('unregistered.html')

@main.route("/about")
def about():
	if current_user.is_authenticated:
		if current_user.temp_image:
			delete_temp_image()
	return render_template('about.html', title='about')

