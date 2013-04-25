from . import app, CONVENIENCE_FEE
from .models import Guardian, AgeGroup, Park
from .util import format_currency, format_phone_num, format_postal_code

from flask import render_template, send_file, Response, stream_with_context, redirect
from flask.ext.security import login_required, roles_accepted, current_user

from subprocess import call

from fdfgen import forge_fdf

import stripe
import redis

import os.path, os

stripe_cache = redis.StrictRedis("localhost")

@app.route('/')
def home():
  return render_template("index.html")

@app.route('/verify')
@app.route('/signup')
@app.route('/register')
@app.route('/checkout')
def redirect_to_home():
  return redirect("/")

def _paid_park_fee(park, customer_id, players):
  paid_total = 0
  owed_total = 0

  if stripe_cache.exists(customer_id):
    paid_total = int(stripe_cache.get(customer_id))
  else:
    charges = stripe.Charge.all(customer=customer_id)

    for charge in enumerate(charges.data):
      paid_total += charge[1].amount

    stripe_cache.set(customer_id, paid_total)
    stripe_cache.expire(customer_id, 60*60*24) # One day

  for player in players:
    age_group = AgeGroup.query.get_or_404(player.age_group_id)
    owed_total += age_group.basefee + age_group.userfee + CONVENIENCE_FEE

  owed_total += park.fee

  return owed_total == paid_total

@app.route("/api/all/")
@login_required
@roles_accepted("admin")
def view_all_csv():
  def generate():
    yield ",".join([
      "GID", "Email", "GFN", "GLN", "Apt", "Street", "City", "Province",
      "Postal Code", "Verified Address", "Primary Phone",
      "Secondary Phone", "Marketing", "Volunteering", "PID", "PFN",
      "PLN", "Verified DOB", "DOB", "Gender", "Played Before",
      "Played Years", "Played Position", "Notes", "Pooling", "All-Star",
      "EC Name", "EC Number", "Paid", "Paid At", "Park", "Age Group",
      "Base Fee", "User Fee", "Park Fee", "Sport"
    ]) + os.linesep

    for guardian in Guardian.query.all():
      if guardian.customer_id == "" or guardian.park_id == None:
        continue

      park = Park.query.get_or_404(guardian.park_id)
      players = [p for p in guardian.players if p.paid]
      fee = _paid_park_fee(park, guardian.customer_id, players)

      for player in players:
        age_group = AgeGroup.query.get_or_404(player.age_group_id)
        park_fee = park.fee if fee else 0

        yield ",".join(map(lambda x: "\"%s\"" % str(x), [
          guardian.id,
          guardian.email,
          guardian.first_name,
          guardian.last_name,
          guardian.apt,
          guardian.street,
          guardian.city,
          guardian.province,
          guardian.postal_code,
          guardian.verified_addr,
          guardian.primary_phone,
          guardian.secondary_phone,
          guardian.marketing,
          guardian.volunteering,
          player.id,
          player.first_name,
          player.last_name,
          player.verified_dob,
          player.date_of_birth,
          player.gender,
          player.played_before,
          player.played_years,
          player.played_position,
          player.notes,
          player.pooling,
          player.allstar,
          player.ec_name,
          player.ec_num,
          player.paid,
          player.paid_at,
          park.name,
          age_group.name,
          format_currency(age_group.basefee),
          format_currency(age_group.userfee),
          format_currency(park_fee),
          age_group.sport
        ])) + os.linesep

        fee = False

  return Response(stream_with_context(generate()), mimetype="text/csv")

def generate_receipt(id):
  guardian = Guardian.query.get_or_404(id)
  park = Park.query.get_or_404(guardian.park_id)

  waivers_folder = app.config["WAIVERS_FOLDER"]
  waiver_template = os.path.join(waivers_folder, "waiverformtemplate.pdf")
  players = [p for p in guardian.players if p.paid and p.verified_dob]
  output_paths = []

  if guardian.customer_id == "" or len(players) == 0 or not guardian.verified_addr:
    return "No players registered and/or verified", 418

  fee = _paid_park_fee(park, guardian.customer_id, players)

  for player in players:
    age_group = AgeGroup.query.get_or_404(player.age_group_id)
    park_fee = park.fee if fee else 0
    fields = [
      ("park", park.name.title()),
      ("last_name", player.last_name.title()),
      ("first_name", player.first_name.title()),
      ("date_of_birth", player.date_of_birth),
      ("gender", player.gender),
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
      ("notes", player.notes.replace("(", "").replace(")", "")),
      ("pooling", player.pooling.replace("(", "").replace(")", "")),
      ("played_before", "Yes" if player.played_before else "No"),
      ("played_num_years", player.played_years if player.played_before else ""),
      ("played_position", player.played_position),
      ("age_group", age_group.name),
      ("pool", "Yes" if len(player.pooling) > 0 else "No"),
      ("timestamp", player.paid_at.strftime("%Y-%m-%d %H:%M:%S")),
      ("basefee", format_currency(age_group.basefee)),
      ("userfee", format_currency(age_group.userfee)),
      ("parkfee", format_currency(park_fee)),
      ("onlinefee", format_currency(CONVENIENCE_FEE)),
      ("total", format_currency(age_group.basefee + age_group.userfee + park_fee + CONVENIENCE_FEE)),
      ("guardian_name", guardian.get_full_name().title()),
      ("date", player.paid_at.strftime("%Y-%m-%d")),
      ("gid", "G{0:06d}".format(guardian.id)),
      ("pid", "P{0:06d}".format(player.id)),
      ("tax_year", "2013")
    ]

    fdf_path = os.path.join(waivers_folder, "P%d.fdf" % player.id)
    output_path = os.path.join(waivers_folder, "P%d.pdf" % player.id)

    fdf = forge_fdf("", fields, [], [], [])
    fdf_file = open(fdf_path, "w")
    fdf_file.write(fdf)
    fdf_file.close()

    call("pdftk %s fill_form %s output %s flatten" % (waiver_template, fdf_path, output_path), shell=True)

    output_paths.append(output_path)

    # Fees are only applied once per family.
    fee = False

  output_path = os.path.join(waivers_folder, "G%d.pdf" % id)

  call("pdftk %s cat output %s" % (" ".join(output_paths), output_path), shell=True)
  
  return send_file(output_path)

@app.route("/api/receipt/")
@login_required
def view_receipt():
  return generate_receipt(current_user.id)

@app.route("/api/receipt/<int:id>")
@login_required
@roles_accepted("admin", "moderator")
def view_receipt_by_id(id):
  return generate_receipt(id)
