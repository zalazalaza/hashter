from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.validators import DataRequired

class PostForm(FlaskForm):
	title = StringField('title', validators=[DataRequired()])
	content = TextAreaField('content', validators=[DataRequired()])
	picture = FileField('photo', validators=[FileAllowed(['jpg', 'png', 'gif'])])
	key = StringField('key', validators=[Length(min=0, max=20)])
	submit = SubmitField('post')

class CommentForm(FlaskForm):
	content = TextAreaField('reply', validators=[DataRequired()])
	key = StringField('key to encrypt comment', validators=[Length(min=0, max=20)])
	submit = SubmitField('add reply')

class DecryptForm(FlaskForm):
	key = StringField('key', validators=[DataRequired()])
	submit = SubmitField('decrypt?')

