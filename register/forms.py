from flask.ext.wtf import Form, TextField, PasswordField, Required, EqualTo, Length, Email, Regexp, BooleanField, Optional, DateField, IntegerField, SelectField, TextAreaField
from flask.ext.wtf.html5 import EmailField, TelField

from wtforms import ValidationError

from models import AgeGroup, Guardian

def validate_email_unique(form, field):
	if Guardian.query.filter_by(email=field.data).first() != None:
		raise ValidationError("Email must be unique")

class RegistrationForm(Form):
	email = EmailField("Email", validators=[Required(), Email(), validate_email_unique])
	password = PasswordField("Password", validators=[
		Required(),
		EqualTo("confirm", message="Passwords must match.")
	])
	confirm = PasswordField("Confirm Password")

	first_name = TextField("Guardian's First Name", validators=[Required()])
	last_name = TextField("Guardian's Last Name", validators=[Required()])

	apt = TextField("Apt")
	street = TextField("Street Address", validators=[Required(), Regexp("^\d+", message="Please enter in your full address.")])
	city = TextField("City", validators=[Required()])
	#province = TextField("Province", validators=[Required()], default="ON")
	postal_code = TextField("Postal Code", validators=[Required(), Regexp("^\w{1}\d{1}\w{1}\s{0,1}\d{1}\w{1}\d{1}$")])

	primary_phone = TelField("Primary Phone", validators=[Required()])
	secondary_phone = TelField("Secondary Phone", validators=[Optional()])

	marketing = BooleanField("I'd like to receive emails from N.A.S.C. Soccer, Softball, and their affiliates", default=True)
	volunteering = BooleanField("I'd like to volunteer, please contact me with information on how to volunteer")

PLAYED_YEARS = zip(map(str, range(20)), map(str, range(20)))
GENDERS = [("M", "Male"), ("F", "Female")]

AGE_GROUPS = [(ag.id, ag.name) for ag in AgeGroup.query.all()]

class PlayerRegistrationForm(Form):
	first_name = TextField("Child's First Name", validators=[Required()])
	last_name = TextField("Child's Last Name", validators=[Required()])
	date_of_birth = TextField("Date of Birth", validators=[Required()])

	gender = SelectField("Gender", choices=GENDERS)
	age_group_id = SelectField("Program", choices=AGE_GROUPS, coerce=int)

	played_before = BooleanField("Played Before")
	played_years = SelectField("Number of Years", choices=PLAYED_YEARS)
	played_position = TextField("Position")

	osa_another_country = BooleanField("Played in Another Country")
	osa_what_year = TextField("Year")
	osa_what_country = TextField("Country")
	osa_what_club = TextField("Club Name")

	notes = TextAreaField("Notes")
	pooling = TextAreaField("Pooling")

	allstar = BooleanField("All-Star/Selects", description="Please send me information about the All-Star/Selects program")

	ec_name = TextField("Name", validators=[Required()])
	ec_num = TelField("Number", validators=[Required()])
