from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import current_user
from hashter.models import User


class RegistrationForm(FlaskForm):
	username = StringField('username', validators=[DataRequired(),
										Length(min=2, max=20) ])
	email = StringField('email', validators=[DataRequired(), Email()])
	invitation = StringField('invitation string')
	password = PasswordField('password', validators=[DataRequired()])
	confirm_password = PasswordField('confirm password', validators=[DataRequired(), EqualTo('password')] )
	submit = SubmitField('initiate')

	def  validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('choose a different username')

	def  validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('choose a different email')


class LoginForm(FlaskForm):
	email = StringField('email', validators=[DataRequired(), Email()])
	password = PasswordField('password', validators=[DataRequired()])
	remember = BooleanField('remember me')
	submit = SubmitField('login')

class UpdateAccountForm(FlaskForm):
	username = StringField('username', validators=[DataRequired(),
										Length(min=2, max=20) ])
	email = StringField('email', validators=[DataRequired(), Email()])
	picture = FileField('photo', validators=[FileAllowed(['jpg', 'png'])])
	rotate = BooleanField('rotate image')
	display = BooleanField('display change dark/light')
	submit = SubmitField('rebuild')

	def  validate_username(self, username):
		if username.data != current_user.username:
			user = User.query.filter_by(username=username.data).first()
			if user:
				raise ValidationError('choose a different username')

	def  validate_email(self, email):
		if email.data != current_user.email:
			user = User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError('choose a different email')

class RequestResetForm(FlaskForm):
	email = StringField('email', validators=[DataRequired(), Email()])
	submit = SubmitField('bad memory?')

	def  validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is None:
			raise ValidationError('were you invited?')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('password', validators=[DataRequired()])
	confirm_password = PasswordField('confirm password', validators=[DataRequired(), EqualTo('password')] )
	submit = SubmitField('begin')


class InviteFriendForm(FlaskForm):
	email = StringField('email', validators=[DataRequired(), Email()])
	submit = SubmitField('initiate')

class CreateInviteForm(FlaskForm):
	submit = SubmitField('generate string')