from flask.ext.security import UserMixin, RoleMixin
from flask.ext.sqlalchemy import SQLAlchemy

from datetime import datetime

db = SQLAlchemy()

roles_users = db.Table('roles_users',
  db.Column('guardian_id', db.Integer(), db.ForeignKey('guardian.id')),
  db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Guardian(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)

  # Login details
  email = db.Column(db.String(255), unique=True)
  password = db.Column(db.String(255))

  # Name
  first_name = db.Column(db.String(63))
  last_name = db.Column(db.String(63))

  # Address
  apt = db.Column(db.String(15))
  street = db.Column(db.String(255))
  city = db.Column(db.String(63))
  province = db.Column(db.String(2))
  postal_code = db.Column(db.String(6))

  verified_addr = db.Column(db.Boolean(), default=False)
  verified_addr_doc = db.Column(db.Integer, db.ForeignKey("upload.id"))

  # Contact Numbers
  primary_phone = db.Column(db.String(10))
  secondary_phone = db.Column(db.String(10))

  # Additional Stuff
  marketing = db.Column(db.Boolean())
  volunteering = db.Column(db.Boolean())

  # Housekeeping
  active = db.Column(db.Boolean())
  confirmed_at = db.Column(db.DateTime())
  roles = db.relationship('Role', secondary=roles_users,
    backref=db.backref('users', lazy='dynamic'))

  players = db.relationship("Player", backref="guardian", lazy="dynamic")
  park_id = db.Column(db.Integer, db.ForeignKey("park.id"))

  customer_id = db.Column(db.String(32))

  def get_full_name(self):
    return " ".join([self.first_name, self.last_name])

class Player(db.Model):
  id = db.Column(db.Integer, primary_key=True)

  first_name = db.Column(db.String(63))
  last_name = db.Column(db.String(63))

  verified_dob = db.Column(db.Boolean(), default=False)
  verified_dob_doc = db.Column(db.Integer, db.ForeignKey("upload.id"))

  date_of_birth = db.Column(db.Date())
  gender = db.Column(db.String(1))

  played_before = db.Column(db.Boolean())
  played_years = db.Column(db.String(63))
  played_position = db.Column(db.String(63))

  osa_another_country = db.Column(db.Boolean())
  osa_what_year = db.Column(db.Integer())
  osa_what_country = db.Column(db.String(255))
  osa_what_club = db.Column(db.String(255))

  notes = db.Column(db.String(1024))
  pooling = db.Column(db.String(1024))

  allstar = db.Column(db.Boolean())

  ec_name = db.Column(db.String(63))
  ec_num = db.Column(db.String(10))

  guardian_id = db.Column(db.Integer, db.ForeignKey("guardian.id"))
  age_group_id = db.Column(db.Integer, db.ForeignKey("age_group.id"))

  paid = db.Column(db.Boolean())
  active = db.Column(db.Boolean())

  paid_at = db.Column(db.DateTime)
  confirmed_at = db.Column(db.DateTime)

  def get_full_name(self):
    return " ".join([self.first_name, self.last_name])

class Park(db.Model):
  id = db.Column(db.Integer(), primary_key=True)
  name = db.Column(db.String(80), unique=True)
  address = db.Column(db.String(255))
  fee = db.Column(db.Integer())

class ParkStreet(db.Model):
  id = db.Column(db.Integer(), primary_key=True)
  name = db.Column(db.String(255))
  park_id = db.Column(db.Integer, db.ForeignKey("park.id"))

  #__tablename__ = "park_street"

class Role(db.Model, RoleMixin):
  id = db.Column(db.Integer(), primary_key=True)
  name = db.Column(db.String(80), unique=True)
  description = db.Column(db.String(255))

class AgeGroup(db.Model):
  id = db.Column(db.Integer(), primary_key=True)
  name = db.Column(db.String(32))
  start = db.Column(db.Date())
  end = db.Column(db.Date())
  basefee = db.Column(db.Integer())
  userfee = db.Column(db.Integer())
  sport = db.Column(db.String(32))
  gender = db.Column(db.String(2))

  players = db.relationship("Player", backref="agegroup", lazy="dynamic")

class Payment(db.Model):
  id = db.Column(db.String(32), primary_key=True)
  guardian_id = db.Column(db.Integer, db.ForeignKey("guardian.id"))
  amount = db.Column(db.Integer())
  fee = db.Column(db.Integer())
  paid = db.Column(db.Boolean)
  paid_at = db.Column(db.DateTime)
