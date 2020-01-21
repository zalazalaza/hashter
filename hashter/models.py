from hashter import db, login_manager
from flask import current_app
from datetime import datetime
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


tribe = db.Table('tribe',
	db.Column('first_user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('second_user_id', db.Integer, db.ForeignKey('user.id'))
)

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	image_file = db.Column(db.String(20), nullable=False, default='tenofcups.png')
	password = db.Column(db.String(60), nullable=False)
	text_invitations = db.relationship('Invitation', backref='creator', lazy=True)
	invitations = db.Column(db.Integer)
	invite_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
	temp_image = db.Column(db.String(60))
	members = db.Column(db.Integer, nullable=False)
	display = db.Column(db.Integer, nullable=False, default=1)
	posts = db.relationship('Post', backref='author', lazy=True)
	comments = db.relationship('Comment', backref='author', lazy=True)
	village = db.relationship('User', secondary=tribe, 
									primaryjoin=id==tribe.c.first_user_id, 
									secondaryjoin=id==tribe.c.second_user_id,
									backref='tribe', lazy=True)

	def get_reset_token(self, expires_sec=1800):
		s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'user_id': self.id}).decode('utf-8')

	def get_invitation_token(self, email, expires_sec=604800):
		s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'user_id': self.id, 'email':email}).decode('utf-8')

	@staticmethod	
	def verify_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			user_id = s.loads(token)['user_id']
		except:
			return None
		return User.query.get(user_id)

	@staticmethod	
	def verify_invite_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			user_email = s.loads(token)['email']
		except:
			return None
		return User.query.filter_by(email=user_email).first()


	def __repr__(self):
		return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(100), nullable=False)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	content = db.Column(db.Text, nullable=False)
	short_content = db.Column(db.Text(600), nullable=False)
	length = db.Column(db.Integer)
	image_file = db.Column(db.String(20))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	comments = db.relationship('Comment', backref='post', lazy=True)
	encryption = db.Column(db.Boolean, nullable=False)

	def __repr__(self):
		return f"Post('{self.title}','{self.date_posted}')"

class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	content = db.Column(db.Text, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

	def __repr__(self):
		return f"Comment('{self.id}', '{self.date_posted}')"

class Invitation(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	invitation = db.Column(db.String, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __repr__(self):
		return f"Invitation('{self.id}', '{self.invitation}')"

