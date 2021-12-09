from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, validators, DateTimeField 
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from data import skills_set
from flask_bootstrap import Bootstrap

class LoginForm(FlaskForm):
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(('Password'), validators=[
                             DataRequired(), Length(min=8, max=80)])
    submit = SubmitField(('Sign In'))




class RegistrationForm(FlaskForm):
    first_name = StringField(('First Name'), validators=[DataRequired()])
    last_name = StringField(('Last Name'), validators=[DataRequired()])
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(('Password'), validators=[
                             DataRequired(), Length(min=8, max=80)])
    confirm_password = PasswordField(('Confirm Password'), validators=[
                                     DataRequired(), EqualTo('password')])
    submit = SubmitField(('Register'))


class EditProfileForm(FlaskForm):
    first_name = StringField(('First Name'), validators=[DataRequired()])
    last_name = StringField(('Last Name'), validators=[DataRequired()])
    email = StringField(('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(('Password'), validators=[
                             DataRequired(), Length(min=8, max=80)])
    confirm_password = PasswordField(('Confirm Password'), validators=[
                                     DataRequired(), EqualTo('password')])
    submit = SubmitField(('Submit'))


class EditMajorForm(FlaskForm):
    major = StringField(('Major'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))


class EditMinorForm(FlaskForm):
    minor = StringField(('Minor'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))


class AddClassForm(FlaskForm):
    course = StringField(('Class'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))


class RemoveClassForm(FlaskForm):
    course = StringField(('Class'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))


class EditExpForm(FlaskForm):
    school = StringField(('School'), validators=[DataRequired()])
    year = StringField(('Year'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))

class AddSkillForm(FlaskForm):
    skill = SelectField(u'Field name', choices = skills_set, validators = [DataRequired()])
    submit = SubmitField(('Add Skill'))

class AddOrgSkillForm(FlaskForm):
    skill = SelectField(u'Field name', choices = skills_set, validators = [DataRequired()])
    submit = SubmitField(('Add Skill'))

class CreateOrgForm(FlaskForm):
    title = StringField(('Title'), validators=[DataRequired()])
    industry = StringField(('Industry'), validators=[DataRequired()])
    location = StringField(('Location'), validators=[DataRequired()])
    size = StringField(('Size'), validators=[DataRequired()])
    description = StringField(('Description'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))

class CreatePostForm(FlaskForm):
    dropdown = SelectField('What org are you posting for?', choices=[], default=None)
    title = StringField(('Title'), validators=[DataRequired()])
    body = StringField(('Description'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))

class CreateJobForm(FlaskForm): 
    title = StringField(('Position'), validators=[DataRequired()])
    description = StringField(('Job Description'), validators=[DataRequired()])
    submit = SubmitField(('Submit'))

class ScheduleInterviewForm(FlaskForm): 
    location = StringField(('Location'), validators=[DataRequired()])
    rounds = IntegerField('Round', [validators.NumberRange(min=0, max=4)])
    datetime = DateTimeField('Select a Date and Time (%Y-%M-%D %H:%M:%S)', validators=[DataRequired()])
    submit = SubmitField(('Submit'))