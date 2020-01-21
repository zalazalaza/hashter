import os
import secrets
import base64
from PIL import Image
from flask import current_app, url_for
from flask_mail import Message
from hashter import mail, db
from flask_login import current_user
from Cryptodome.Random import get_random_bytes


def generateInvite():
	invite_bytes = get_random_bytes(60)
	invitation = base64.b64encode(invite_bytes).decode('utf-8')
	return invitation

def delete_temp_image():
	path = os.path.join(current_app.root_path, 'static/post_pics', current_user.temp_image)
	if os.path.isfile(path):
		try:
			os.remove(os.path.join(current_app.root_path, 'static/post_pics', current_user.temp_image))
			current_user.temp_image = None
			db.session.commit()
		except:
			pass

def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_fn = random_hex + f_ext
	picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
	output_size = (300,300)
	i = Image.open(form_picture)
	i.thumbnail(output_size)
	i.save(picture_path)
	return picture_fn


def rotate_picture():
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(current_user.image_file)
	new_picture_fn = random_hex + f_ext
	new_picture_path = os.path.join(current_app.root_path, 'static/profile_pics', new_picture_fn)
	picture_path = os.path.join(current_app.root_path, 'static/profile_pics', current_user.image_file)
	im = Image.open(picture_path)
	im.rotate(90).save(new_picture_path)
	return new_picture_fn

def send_reset_email(user):
	token = user.get_reset_token()
	msg = Message('amnesia', 
				sender='noreply@hashter.org', 
				recipients=[user.email])
	msg.body = f'''the slate is blank after this

{url_for('users.reset_token', token=token, _external=True)}

nothing to see here.'''
	mail.send(msg)

def send_invite_email(user, email):
	if current_user.temp_image:
		os.remove(os.path.join(current_app.root_path, 'static/post_pics', current_user.temp_image))
		current_user.temp_image = None
		db.session.commit()
	token_email = email
	token = user.get_invitation_token(token_email)
	msg = Message('lucidity',
					sender='noreply@hashter.org',
					recipients=[email])
	msg.body = f''' an invitation to hashter.org. re-collect
{url_for('users.token_register', token=token, _external=True)}

beyond...'''
	mail.send(msg)

def add_villager(user):
	user.members = user.members + 1
	db.session.commit()
	

def ostracize(user):
	user.members = user.members - 1
	db.session.commit()

