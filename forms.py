from flask.ext.wtf import Form, TextField, PasswordField, Required, EqualTo, Length, Email, Regexp, BooleanField, Optional, DateField, IntegerField, SelectField, TextAreaField
from flask.ext.wtf.html5 import EmailField, TelField

from wtforms import ValidationError

from models import AgeGroup, Guardian

def validate_email_unique(form, field):
	if Guardian.query.filter_by(email=field.data).first() != None:
		raise ValidationError("Email must be unique")

class RegistrationForm(Form):
	email = EmailField("Email", validators=[Required(), Email(), validate_email_unique], default="rdrake@rdrake.org")
	password = PasswordField("Password", validators=[
		Required(),
		EqualTo("confirm", message="Passwords must match.")
	])
	confirm = PasswordField("Confirm Password")

	first_name = TextField("First Name", validators=[Required()], default="Richard")
	last_name = TextField("Last Name", validators=[Required()], default="Drake")

	apt = TextField("Apt")
	street = TextField("Street", validators=[Required()], default="959 Renfrew Court")
	city = TextField("City", validators=[Required()], default="Oshawa")
	#province = TextField("Province", validators=[Required()], default="ON")
	postal_code = TextField("Postal Code", validators=[Required(), Regexp("^\w{1}\d{1}\w{1}\s{0,1}\d{1}\w{1}\d{1}$")], default="L1J 6L2")

	primary_phone = TelField("Primary Phone", validators=[Required()], default="9054423152")
	secondary_phone = TelField("Secondary Phone", validators=[Optional()])

	marketing = BooleanField("I'd like to receive emails from N.A.S.C. Soccer, Softball, and their affiliates", default=True)
	volunteering = BooleanField("I'd like to volunteer, please contact me with information on how to volunteer", default=False)

PLAYED_YEARS = zip(map(str, range(20)), map(str, range(20)))
GENDERS = [("M", "Male"), ("F", "Female")]

AGE_GROUPS = [(ag.id, ag.name) for ag in AgeGroup.query.all()]

class PlayerRegistrationForm(Form):
	first_name = TextField("First Name", validators=[Required()], default="Jonathan")
	last_name = TextField("Last Name", validators=[Required()], default="Drake")

	date_of_birth = TextField("Date of Birth", validators=[Required()], default="1999-02-01")

	gender = SelectField("Gender", choices=GENDERS)
	age_group_id = SelectField("Program", choices=AGE_GROUPS, coerce=int)
	#gender = TextField("Gender", validators=[Required()], default="M")

	played_before = BooleanField("Played Before")
	#played_years = IntegerField("Number of Years", default=0)
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
