from . import app, db, mail, CONVENIENCE_FEE, STRIPE_KEYS
from .forms import RegistrationForm, PlayerRegistrationForm
from .models import Guardian, Role, Player, AgeGroup, Park, ParkStreet, Payment
from .util import clean_phone_num, format_currency, format_phone_num, format_postal_code

from flask import request, render_template, flash, jsonify, redirect, send_from_directory, send_file
from flask.ext.mail import Message
from flask.ext.security import login_required, roles_accepted, current_user, registerable
from flask.ext.uploads import save, Upload

from collections import defaultdict
from datetime import datetime

from geopy import geocoders
from fdfgen import forge_fdf

import stripe

import os.path

g = geocoders.Google()

@app.route('/')
def home():
	return render_template("index.html")

def _alert_no_park(form):
	msg = Message("No Park Determined!", recipients=["richard.drake@nascsoccer.org"])
	msg.body = "Look into %s %s" % (form.first_name.data, form.last_name.data)

	mail.send(msg)

@app.route("/signup", methods=["GET", "POST"])
def signup():
	form = RegistrationForm(request.form)
	park_id = None
	
	if request.method == "POST":
		if form.validate():
			addr = " ".join([form.street.data, form.city.data, "ON", form.postal_code.data])
			try:
				place, (lat, lng) = g.geocode(addr)
				street = " ".join(place.split(",")[0].strip().split()[1:])
				park_street = ParkStreet.query.filter_by(name=street).first()

				if park_street:
					park_id = park_street.park_id
				else:
					_alert_no_park(form)
			except:
				_alert_no_park(form)

			registerable.register_user(
				email = form.email.data,
				password = form.password.data,
				first_name = form.first_name.data,
				last_name = form.last_name.data,
				apt = form.apt.data,
				street = form.street.data,
				city = form.city.data,
				province = "ON",
				postal_code = form.postal_code.data.replace(" ", "").upper(),
				verified_addr = False,
				primary_phone = clean_phone_num(form.primary_phone.data),
				secondary_phone = clean_phone_num(form.secondary_phone.data),
				marketing = form.marketing.data,
				park_id = park_id,
				active = True
			)
			db.session.commit()

			return redirect("/login")
		else:
			flash("Please correct the errors below.", "error")

	return render_template("signup.html", form=form, title="Sign Up")

@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
	form = PlayerRegistrationForm(request.form)

	if request.method == "POST" and form.validate():
		player = Player(
			first_name = form.first_name.data,
			last_name = form.last_name.data,
			date_of_birth = form.date_of_birth.data,
			gender = form.gender.data,
			played_before = form.played_before.data,
			played_years = form.played_years.data,
			played_position = form.played_position.data,
			osa_another_country = form.osa_another_country.data,
			osa_what_year = form.osa_what_year.data,
			osa_what_country = form.osa_what_country.data,
			osa_what_club = form.osa_what_club.data,
			notes = form.notes.data,
			pooling = form.pooling.data,
			allstar = form.allstar.data,
			ec_name = form.ec_name.data,
			ec_num = clean_phone_num(form.ec_num.data),
			age_group_id = form.age_group_id.data,
			guardian_id = current_user.id,
			paid = False,
			active = True
		)

		db.session.add(player)

		db.session.commit()
		
		flash("Successfully registered player!")

		return redirect("/success")

	return render_template("register.html", form=form, title="Register Player")

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
	# All players who have not been paid for already should show up.
	players = [player for player in current_user.players if not player.paid]
	fees = defaultdict(list)

	# Enumerate through all of the players and create descriptions of each
	# of t)e fees.
	for player in players:
		ag = AgeGroup.query.get(player.age_group_id)
		p = fees[player.get_full_name()]

		p.append(["%s - %s" % (ag.name, ag.sport), ag.basefee])
		p.append(["User Fee<sup>1</sup>", ag.userfee])
		p.append(["Convenience Fee<sup>2</sup>", CONVENIENCE_FEE])
	
	if len(players) > 0 and current_user.customer_id is None or current_user.customer_id == "":
		if current_user.park_id:
			park = Park.query.get(current_user.park_id)
			fees["Other"].append(["Park Fee - %s<sup>3</sup>" % park.name, park.fee])

	# Total everything up.
	total = 0

	for player in fees:
		for (title, fee) in fees[player]:
			total += fee

	if request.method == "POST":
		# Bill them.  Well, at least try to.
		try:
			if not current_user.customer_id:
				customer = stripe.Customer.create(
					email = current_user.email,
					card = request.form["stripeToken"]
				)

				current_user.customer_id = customer.id
				db.session.commit()

			charge = stripe.Charge.create(
				customer = current_user.customer_id,
				amount = total,
				currency = "cad",
				description = "Registration fee"
			)

			# If the charge went through, mark all of the players as paid.
			if charge.paid:
				payment = Payment(
					id=charge.id,
					guardian_id = current_user.id,
					amount = charge.amount,
					fee = charge.fee,
					paid = charge.paid,
					paid_at = datetime.now()
				)

				db.session.add(payment)

				for player in players:
					player.paid = True
					player.paid_at = datetime.now()

				db.session.commit()

				msg = Message("Your Registration Was Successful", recipients=[current_user.email])
				msg.body = "We have successfully received your payment of $%0.2f.  Please complete the verification step by submitting supporting documentation to the following page:\n\nhttps://register.nascsoccer.org/verify" % (charge.amount / 100)

				mail.send(msg)

				# Also get verification.
				return redirect("/verify")
		except stripe.CardError as e:
			flash("%s.  Please try again." % e.message, "error")
	
	# If they haven't paid yet, ask them to.
	return render_template("checkout.html", total=total, fees=fees, key=STRIPE_KEYS["publishable_key"])

@app.route("/success")
@login_required
def success():
	return render_template("success.html")

@app.route("/verify")
@login_required
def verify():
	players_verified = [p.verified_dob for p in current_user.players]
	done = current_user.verified_addr and False not in players_verified

	return render_template("verify.html", done=done)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
	if request.method == "POST":
		photo = request.files["photo"]

		# Only save images, ignore any other uploads.
		if "image" in photo.mimetype or "application/pdf" in photo.mimetype:
			save(photo)

			last_inserted_id = Upload.query.all()[-1].id

			player_id = request.form.get("player_id", None)
			player_ids = [player.id for player in current_user.players]

			if player_id and int(player_id) in player_ids:
				Player.query.get(player_id).verified_dob_doc = last_inserted_id
			elif not player_id:
				current_user.verified_addr_doc = last_inserted_id

			msg = Message("Registration Needs Verifying", recipients=["richard.drake@nascsoccer.org"])
			msg.body = "Guardian %d, submitted verification!" % current_user.id

			mail.send(msg)

			# If none of the above are executed, chances are they're trying to
			# change the documentation for a player they haven't registered.

			db.session.commit()
		else:
			flash("Did not receive an image file (PNG, JPEG, GIF, TIFF, etc) or PDF.  Please try again.")

	return redirect("/verify")

# For this to work, need to add role and user to role.
"""
from app import Guardian, Role, db, user_datastore
user = Guardian.query.filter_by(email='rdrake@rdrake.org').first()
user_datastore.create_role(name="admin", description="Administrator, can do anything")
user_datastore.create_role(name="moderator", description="Moderates proof of address/dob/etc.")
db.session.commit()
user_datastore.add_role_to_user(user, "admin")
db.session.commit()
"""
@app.route("/moderate")
@login_required
@roles_accepted("admin", "moderator")
def moderate():
	# Want all addresses that are unverified but have documentation.
	addresses = Guardian.query.filter_by(verified_addr=False).filter(Guardian.verified_addr_doc != None)
	# Players too.
	players = Player.query.filter(Player.verified_dob != True).filter(Player.verified_dob_doc != None)

	return render_template("moderate.html", addresses=addresses, players=players)

@app.route("/api/upload/<int:id>")
@login_required
@roles_accepted("admin", "moderator")
def view_upload(id):
	upload = Upload.query.get_or_404(id)
	return send_from_directory(app.config["UPLOADS_FOLDER"], upload.name)

@app.route("/api/waiver/<int:id>")
@login_required
@roles_accepted("admin", "moderator")
def view_waiver(id):
	player = Player.query.get_or_404(id)
	guardian = Guardian.query.get_or_404(player.guardian_id)
	age_group = AgeGroup.query.get_or_404(player.age_group_id)
	park = Park.query.get_or_404(guardian.park_id)

	waivers_folder = app.config["WAIVERS_FOLDER"]
	waiver_template = os.path.join("register", "templates", "waiverformtemplate.pdf")

	fields = [
		("park", park.name.title()),
		("last_name", player.last_name.title()),
		("first_name", player.first_name.title()),
		("date_of_birth", player.date_of_birth),
		("street", guardian.street.title()),
		("apt", guardian.apt),
		("city", guardian.city.title()),
		("province", guardian.province),
		("postal_code", format_postal_code(guardian.postal_code)),
		("email", guardian.email),
		("primary_phone", format_phone_num(guardian.primary_phone)),
		("secondary_phone", format_phone_num(guardian.secondary_phone)),
		("ec_name", player.ec_name.title()),
		("ec_num", format_phone_num(player.ec_num)),
		("notes", player.notes),
		("pooling", player.pooling),
		("played_before", "Yes" if player.played_before else "No"),
		("played_num_years", player.played_years if player.played_before else ""),
		("played_position", player.played_position),
		("age_group", age_group.name),
		("pool", "Yes" if len(player.pooling) > 0 else "No"),
		("timestamp", player.paid_at.strftime("%Y-%m-%d %H:%M:%S")),
		("basefee", format_currency(age_group.basefee)),
		("userfee", format_currency(age_group.userfee)),
		("parkfee", format_currency(park.fee)),
		("onlinefee", format_currency(CONVENIENCE_FEE)),
		("total", format_currency(age_group.basefee + age_group.userfee + park.fee + CONVENIENCE_FEE)),
		("guardian_name", guardian.get_full_name().title()),
		("date", player.paid_at.strftime("%Y-%m-%d"))
	]

	fdf_path = os.path.join(waivers_folder, "%d.fdf" % id)
	output_path = os.path.join(waivers_folder, "%d.pdf" % id)

	fdf = forge_fdf("", fields, [], [], [])
	fdf_file = open(fdf_path, "w")
	print fdf_path
	fdf_file.write(fdf)
	fdf_file.close()

	from subprocess import call

	call("pdftk %s fill_form %s output %s flatten" % (waiver_template, fdf_path, output_path), shell=True)

	return send_file(output_path)

@app.route("/api/verify/player/<int:id>", methods=["POST"])
@login_required
@roles_accepted("admin", "moderator")
def verify_player(id):
	player = Player.query.get_or_404(id)
	player.verified_dob = True
	player.confirmed_at = datetime.now()
	db.session.commit()

	flash("Successfully verified date of birth for %s, %s" % (player.last_name, player.first_name))

	return redirect("/moderate")

@app.route("/api/verify/address/<int:id>", methods=["POST"])
@login_required
@roles_accepted("admin", "moderator")
def verify_address(id):
	guardian = Guardian.query.get_or_404(id)
	guardian.verified_addr = True
	guardian.confirmed_at = datetime.now()
	db.session.commit()

	flash("Successfully verified address for %s" % guardian.get_full_name())

	return redirect("/moderate")

@app.route("/api/programs")
@login_required
def programs():
	gender = request.args["gender"]
	date_of_birth = request.args["date_of_birth"]

	programs = AgeGroup.query.filter(
		date_of_birth <= AgeGroup.end,
		date_of_birth >= AgeGroup.start,
		AgeGroup.gender.like("%%%s%%" % gender)
	).all()

	return jsonify(programs=[{
		"id": program.id,
		"name": program.name,
		"basefee": program.basefee,
		"userfee": program.userfee,
		"sport": program.sport,
		"text": "%s - %s" % (program.name, program.sport)
	} for program in programs])
