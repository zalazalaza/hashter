import base64
import os
from flask import (render_template, current_app, url_for, flash, redirect, request, abort, Blueprint)
from flask_login import current_user, login_required
from hashter import db
from hashter.models import Post, Comment, User
from hashter.posts.forms import PostForm, CommentForm, DecryptForm
from hashter.posts.utils import (save_post_picture, save_encrypted_post_picture, decrypt_picture,
									get_key, encryptAES_CBC, decryptAES_CBC, randomName)
from hashter.users.utils import delete_temp_image


posts = Blueprint('posts', __name__)

@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
	form = PostForm()
	picture_file = None
	if current_user.temp_image:
		delete_temp_image()
	if form.validate_on_submit():
		if form.key.data:
			message = form.content.data
			message_key = get_key(form.key.data)
			if form.picture.data:
				picture_file = save_encrypted_post_picture(message_key, form.picture.data)
			ciphertext = encryptAES_CBC(message_key, message)
			post = Post(title=form.title.data, content=ciphertext, length=len(ciphertext), 
						image_file=picture_file, author=current_user, encryption=True, short_content=ciphertext[:300])
			db.session.add(post)
			db.session.commit()
			flash('a secret', 'success')
		else:
			if form.picture.data:
				picture_file = save_post_picture(form.picture.data)
			post = Post(title=form.title.data, content=form.content.data, length=len(form.content.data), 
						image_file=picture_file, author=current_user, encryption=False, short_content=form.content.data[:500])
			db.session.add(post)
			db.session.commit()
			flash('no key created', 'success')
		return redirect(url_for('main.home'))
	return render_template('create_post.html', title='speak', form=form, legend='speak')

@posts.route("/post/<int:post_id>", methods=['GET','POST'])
@login_required
def post(post_id):
	if current_user.temp_image:
		delete_temp_image()
	form= DecryptForm()
	form2 = CommentForm()
	post = Post.query.get_or_404(post_id)
	comment_encrypted_names = []
	comments = Comment.query.filter_by(post=post)
	for comment in comments:
		name = comment.author.username
		comment_encrypted_name = randomName(name)
		comment_encrypted_names.append(comment_encrypted_name)
	encrypted_name = randomName(post.author.username)
	
	if post.encryption == False:
		form = None
	elif post.encryption == True:
		if post.image_file:
			filename = post.image_file
			user  = current_user
			if form.validate_on_submit():
				post_key = get_key(form.key.data)
				new_image = decrypt_picture(post_key, filename)
				message = decryptAES_CBC(post_key, post.content)
				user.temp_image = new_image
				flash(f'message is { message }', 'whole success')
				db.session.commit()
				return redirect(url_for('posts.decrypted', post_id=post.id))
		if form.validate_on_submit():
			post_key = get_key(form.key.data)
			post_ciphertext = post.content
			message = decryptAES_CBC(post_key, post_ciphertext)
			flash(f'message is { message }', 'success')
		elif form.errors:
			flash(f'mustnt be it', 'success')
	if form2.validate_on_submit():
		if form2.key.data:
			message = form2.content.data
			comment_key = get_key(form2.key.data)
			ciphertext = encryptAES_CBC(comment_key, message)
			comment = Comment(content=ciphertext, author=current_user, post=post)
		else:
			comment=Comment(content=form2.content.data, author=current_user, post=post)
		db.session.add(comment)
		db.session.commit()
		flash('comment added', 'success')
		return redirect(url_for('posts.post', post_id=post_id))
	return render_template('post.html', title=post.title, post=post, 
							form=form, comment_encrypted_names=comment_encrypted_names, 
							encrypted_name=encrypted_name, form2=form2, comments=comments)

@posts.route("/post/<int:post_id>/update", methods=['GET','POST'])
@login_required
def update_post(post_id):
	post = Post.query.get_or_404(post_id)
	if current_user.temp_image:
		delete_temp_image()
	if post.author != current_user:
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		if form.key.data:
			message = form.content.data
			message_key = get_key(form.key.data)
			ciphertext = encryptAES_CBC(message_key, message)
			post.title = form.title.data
			post.content = ciphertext
			db.session.commit()
			flash('a secret', 'success')
			return redirect(url_for('posts.post', post_id = post.id))
		else:
			post.title = form.title.data
			post.content = form.content.data
			db.session.commit()
			flash('revolving revolved', 'success')
			return redirect(url_for('posts.post', post_id = post.id))
	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content
	return render_template('create_post.html', title='revolve', form=form, legend='revolve')

@posts.route("/post/<int:post_id>/delete", methods=['GET','POST'])
@login_required
def delete_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403)
	elif post.comments:
		if post.image_file:
			os.remove(os.path.join(current_app.root_path, 'static/post_pics', post.image_file))
			post.image_file = None
		post.content = "(deleted)"
		post.short_content = "(deleted)"
		db.session.commit()
	else:
		if post.image_file:
			os.remove(os.path.join(current_app.root_path, 'static/post_pics', post.image_file))
		db.session.delete(post)
		db.session.commit()
		flash('exitium', 'success')
	return redirect(url_for('main.home'))

@posts.route("/comment/<int:comment_id>/delete", methods=['GET','POST'])
@login_required
def delete_comment(comment_id):
	comment = Comment.query.get_or_404(comment_id)
	if comment.author != current_user:
		abort(403)
	else:
		db.session.delete(comment)
		db.session.commit()
		flash('comment exitium', 'success')
		return redirect(url_for('main.home'))
	

@posts.route("/decrypted/<post_id>", methods=['GET', 'POST'])
@login_required
def decrypted(post_id):
	user = current_user
	post = Post.query.get_or_404(post_id)
	return render_template('decrypted.html', user=current_user, post=post)

@posts.route("/deluge")
def everything():
	if current_user.is_authenticated:
		if current_user.temp_image:
			delete_temp_image()
		tribe = current_user.tribe
		page = request.args.get('page', 1, type=int)
		posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
		encrypted_names = []
		for post in posts.items:
			name = post.author.username
			encrypted_name = randomName(name)
			encrypted_names.append(encrypted_name)

		return render_template('deluge.html', posts=posts, tribe=tribe, encrypted_names=encrypted_names)
	else:
		return render_template('unregistered.html')
