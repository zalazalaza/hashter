
import os
import datetime as dtime
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request ,Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from hashter import db, bcrypt
from hashter.models import User, Post, Comment, Invitation
from hashter.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm, 
								RequestResetForm, ResetPasswordForm, InviteFriendForm, CreateInviteForm)
from hashter.users.utils import (save_picture, send_reset_email,rotate_picture, 
								send_invite_email, generateInvite, delete_temp_image, add_villager, ostracize)

users = Blueprint('users', __name__)

@users.route("/register", methods=['GET','POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('users.logout'))
	form=RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password, members=0)
		db.session.add(user)
		db.session.flush()
		if user.id == 1:
			db.session.commit()
			flash(f'welcome back again zalazalaza your username is {form.username.data} your id is {user.id}', 'success')
			return redirect(url_for('users.login'))
		elif user.id > 1:
			invite_confirm = Invitation.query.filter_by(invitation=form.invitation.data).first()
			if invite_confirm:
				creator = invite_confirm.creator
				user.tribe.append(creator)
				add_villager(user)
				if creator.members < 100:
					creator.tribe.append(user)
					add_villager(creator)
				elif creator.members >= 100:
					flash(f'{ creator.username } has too many friends', 'success')
				db.session.delete(invite_confirm)
				db.session.commit()
				flash(f'account created for {form.username.data}. you can now log in', 'success')
				return redirect(url_for('users.login'))
			else:
				db.session.close()
				flash('wrong code kid', 'success')
				return redirect(url_for('users.register'))
		else:
			flash('whats the password?', 'alert')
			return redirect(url_for('users.register'))
	return render_template('register.html', title='register', form=form)

@users.route("/register/<token>", methods=['GET','POST'])
def token_register(token):
	if current_user.is_authenticated:
		return redirect(url_for('users.logout'))
	user = User.verify_token(token)
	if user is None:
		flash('bad token', 'alert')
		return redirect(url_for('users.unregistered'))
	email_user = User.verify_invite_token(token)
	if email_user:
		flash('email already in use', 'alert')
		return redirect(url_for('users.login'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		
		user_new = User(username=form.username.data, email=form.email.data, password=hashed_password, members=0)
		db.session.add(user_new)
		db.session.commit()
		if user:
			if user.members < 100:
				add_villager(user)
				add_villager(user_new)
				user_new.tribe.append(user)
				user.tribe.append(user_new)
				db.session.commit()
				flash('welcome home', 'success')
			if user.members >= 100:
				user_new.tribe.append(user)
				db.session.commit()
				add_villager(user_new)
				flash(f'you have them but they dont have you. account created { form.username.data }', 'success')
		return redirect(url_for('users.login'))
	return render_template('token_register.html', title='forget something?', form=form)

@users.route("/unregistered", methods=['GET','POST'])
def unregistered():
	if current_user.is_authenticated:
		return redirect(url_for('users.logout'))
	return render_template('unregistered.html', title='no name')

@users.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main.home'))
	form=LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			flash(f'your wish is my command { current_user.username }', 'success')
			return redirect(next_page) if next_page else redirect(url_for('main.home'))
		else:
			flash('login unsuccessful , check yr info', 'bad')

	return render_template('login.html', title='log in', form=form)

@users.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('users.login'))

@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
	if current_user.is_authenticated:
		form = UpdateAccountForm()
		if current_user.temp_image:
			delete_temp_image()
		if form.validate_on_submit():
			if form.picture.data:
				picture_file = save_picture(form.picture.data)
				current_user.image_file = picture_file
			if form.rotate.data:
				picture_file = rotate_picture()
				current_user.image_file = picture_file
			if form.display.data:
				if current_user.display == 1:
					current_user.display = 0
				elif current_user.display == 0:
					current_user.display = 1
				else:
					current_user.display = 0	
			current_user.username = form.username.data
			current_user.email = form.email.data
			db.session.commit()
			flash('your account has been updated', 'alert')
			return redirect(url_for('users.account'))
		elif request.method == 'GET':
			form.username.data = current_user.username
			form.email.data = current_user.email
		image_file = url_for('static', filename='profile_pics/'+ current_user.image_file)
		return render_template('account.html', title='account', 
							image_file=image_file, form=form)
	else:
		return render_template('unregistered')

@users.route("/user/<string:username>")
def user_posts(username):
	if current_user.is_authenticated:
		if current_user.temp_image:
			delete_temp_image()
		page = request.args.get('page', 1, type=int)
		user = User.query.filter_by(username=username).first_or_404()
		posts = Post.query.filter_by(author=user)\
			.order_by(Post.date_posted.desc())\
			.paginate(page=page, per_page=5)
		return render_template('user_posts.html', posts=posts, user=user)
	else:
		return render_template('unregistered.html')

@users.route("/reset_password", methods=['GET','POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('main.home'))
	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('check your email', 'success')
		return redirect(url_for('users.login'))
	return render_template('reset_request.html', title='forget something?', form=form)

@users.route("/reset_password/<token>", methods=['GET','POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.home'))
	user = User.verify_token(token)
	if user is None:
		flash('bad token', 'alert')
		return redirect(url_for('users.reset_request'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user.password = hashed_password
		db.session.commit()
		flash('remembered', 'success')
		return redirect(url_for('users.login'))
	return render_template('reset_token.html', title='forget something?', form=form)

@users.route("/tribe/text", methods=['GET', 'POST'])
@login_required
def hand_invite():
	if current_user.is_authenticated:
		if current_user.temp_image:
			delete_temp_image()
		tribe = current_user.tribe
	form2 = CreateInviteForm()
	if form2.validate_on_submit():
		tdelta = dtime.timedelta(days=30)
		if current_user.invitations:
			stamp = current_user.invite_timestamp + tdelta
			if current_user.id == 1 and current_user.username == "zalazalaza":
				invite = generateInvite()
				invitation = Invitation(invitation=invite, user_id=current_user.id)
				db.session.add(invitation)
				db.session.commit()
				flash(f'hello zalazalaza {invite} is your new code. write it down', 'success')
				return redirect(url_for('users.hand_invite'))

			if stamp >= datetime.utcnow() and current_user.invitations < 10:
				invite = generateInvite()
				invitation = Invitation(invitation=invite, user_id=current_user.id)
				current_user.invitations += 1
				db.session.add(invitation)
				db.session.commit()
				flash(f'{invite} is your new code. write it down. you have {10 - current_user.invitations} invitations left', 'success')
				return redirect(url_for('users.hand_invite'))
			elif stamp < datetime.utcnow():
				invite = generateInvite()
				invitation = Invitation(invitation=invite, user_id=current_user.id)
				current_user.invitations = 1
				current_user.invite_timestamp = datetime.urcnow()
				db.session.add(invitation)
				db.session.commit()
				flash(f'{invite} is your code. Youve been patient and now have 10 more invites', 'success')
				return redirect(url_for('users.hand_invite'))
			elif current_user.invitations >= 10:
				flash('too many too soon', 'success')
				return redirect(url_for('main.home'))
		else:
			invite = generateInvite()
			invitation = Invitation(invitation=invite, user_id=current_user.id)
			current_user.invitations = 1
			current_user.invite_timestamp = datetime.utcnow()
			db.session.add(invitation)
			db.session.commit()
			flash(f'{invite} is your new code. write it down', 'success')
			return redirect(url_for('users.hand_invite'))
	return render_template('hand_tribe.html', title='size', tribe=tribe, form2=form2)


@users.route("/tribe", methods=['GET', 'POST'])
@login_required
def invite():
	if current_user.is_authenticated:
		if current_user.temp_image:
			delete_temp_image()
		tribe = current_user.tribe
		form = InviteFriendForm()
		if form.validate_on_submit():
			tdelta = dtime.timedelta(days=30)
			new_user = User.query.filter_by(email=form.email.data).first()
			if new_user:
				if new_user in current_user.tribe:
					flash(f'{new_user.username} already exists with email {new_user.email} and is in your village')
					return redirect(url_for('users.invite'))
				elif new_user == current_user:
					flash('thats you')
					return redirect(url_for('users.invite'))
				else:
					flash(f'{new_user.username} already exists with email {new_user.email} and has been added to your village')
					current_user.tribe.append(new_user)
					db.session.commit()
					return redirect(url_for('users.invite'))
			if current_user.invitations:
				stamp = current_user.invite_timestamp + tdelta
				if stamp >= datetime.utcnow() and current_user.invitations < 10:
					send_invite_email(current_user, form.email.data)
					current_user.invitations = current_user.invitations + 1
					current_user.invite_timestamp = current_user.invite_timestamp
					db.session.commit()
					flash(f'''invite # {current_user.invitations} counting from {current_user.invite_timestamp} Emailing: {form.email.data}''', 'success')
					return redirect(url_for('main.home'))
				elif stamp < datetime.utcnow() :
					send_invite_email(current_user, form.email.data)
					current_user.invitations = 1
					current_user.invite_timestamp = datetime.utcnow()
					db.session.commit()
					flash(f'new session of invites # {current_user.invitations} counting from {current_user.invite_timestamp} CURRENT TIME IS {datetime.utcnow()}', 'success')
					return redirect(url_for('main.home'))
				else:
					flash('please wait for more invites', 'success')
					return redirect(url_for('main.home'))
			else:
				send_invite_email(current_user, form.email.data)
				current_user.invitations = 1
				current_user.invite_timestamp = datetime.utcnow()
				db.session.commit()
				flash(f'first invite {current_user.invite_timestamp}', 'success')
		return render_template('tribe.html', title='size', tribe=tribe,form=form)

@users.route("/user/<int:user_id>/delete", methods=['GET','POST'])
@login_required
def delete_person(user_id):
	user = User.query.get_or_404(user_id)
	if user in current_user.tribe:
		current_user.tribe.remove(user)
		db.session.commit()
		ostracize(current_user)
		flash(f'exitium { current_user.tribe }', 'success')
		return redirect(url_for('users.invite'))
	else:
		return redirect(url_for('users.invite'))

@users.route("/tribe/<string:username>")
@login_required
def other_tribe(username):
	if current_user.is_authenticated:
		if current_user.temp_image:
			delete_temp_image()
		user = User.query.filter_by(username=username).first_or_404()
		tribe = user.tribe
		if user ==  current_user:
			return redirect(url_for('users.invite'))
		return render_template('other_tribe.html', title='tribe',tribe=tribe, user=user, username=username)

@users.route("/user/<int:user_id>/add", methods=['GET','POST'])
@login_required
def add_person(user_id):
	user = User.query.get_or_404(user_id)
	if user.members < 100:
		if user in current_user.tribe:
			flash(f'double dragon', 'success')
			return redirect(url_for('users.invite'))
		elif user == current_user:
			flash('thats you', 'success')
			return redirect(url_for('main.home'))
		else:
			current_user.tribe.append(user)
			db.session.commit()
			add_villager(current_user)
			flash(f'{ user.username } is now in your village', 'success')
			return redirect(url_for('users.invite'))
	else:
		flash('you got like a hundred computer friends, thats enough. Go outside')
		return redirect(url_for('logout'))



