"""
Form classes for ArtSwap application.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class SignupForm(FlaskForm):
    """Form for user signup."""
    
    username = StringField('Username', 
                          validators=[DataRequired(), Length(min=3, max=30)])
    
    email = StringField('Email', 
                       validators=[DataRequired(), Email(), Length(max=100)])
    
    password = PasswordField('Password', 
                            validators=[DataRequired(), Length(min=6)])
    
    confirm = PasswordField('Confirm Password',
                            validators=[DataRequired(), EqualTo('password')])
    
    def validate_username(self, field):
        """Check if username is already taken."""
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('Username already taken.')
    
    def validate_email(self, field):
        """Check if email is already registered."""
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Email already registered.')


class LoginForm(FlaskForm):
    """Form for user login."""
    
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class ArtPieceForm(FlaskForm):
    """Form for creating/editing an art piece."""
    
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    
    description = TextAreaField('Description')
    
    image = FileField('Upload Artwork', 
                     validators=[
                         FileRequired(),
                         FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
                     ])


class TradeForm(FlaskForm):
    """Form for creating a trade offer."""
    
    sender_art_id = SelectField('Your Artwork', coerce=int, validators=[DataRequired()])
    
    receiver_art_id = HiddenField('Their Artwork', validators=[DataRequired()])
    
    message = TextAreaField('Message to Recipient (Optional)')