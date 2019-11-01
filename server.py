from flask import Flask, request, render_template, redirect, jsonify, session
import requests, json, re
from flask_sqlalchemy import SQLAlchemy

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__)
app.secret_key = "LaunchMobilityFTW"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/test_db2'

db = SQLAlchemy(app)

#abstract to models.py
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True, unique=True)
  email = db.Column(db.String(30), unique=True)
  confirmed = db.Column(db.Boolean, default=False)

  first_name = db.Column(db.String(30))
  middle_name = db.Column(db.String(30))
  last_name = db.Column(db.String(30))
  zip_code = db.Column(db.String(5))

  city = db.Column(db.String(50))
  county = db.Column(db.String(50))
  state = db.Column(db.String(50))

  def __init__(self, email):
    self.email = email

  def __repr__(self):
    return '<User %r>' % self.email

@app.route('/register', methods=['POST'])
def register():
  email = request.form['email']
  errors = []

  #validate email address
  if len(email) < 5:
    errors.append("Email prefix must include atleast 5 characters")
  elif not EMAIL_REGEX.match(email):
    errors.append("Invalid Email Address format")
  else:
    return_res_with_errors(errors)
    user = User.query.filter_by(email=email).first()

    #check db for existing email address
    if user:
      errors.append("User already exists, please choose a unique email address")
      return_res_with_errors(errors)
    else:
      user = User(email)
      db.session.add(user)
      db.session.commit()

      return jsonify(
        email = user.email,
        message = f'User {user.email}, successfully registered, please confirm account'
      )

def return_res_with_errors(errors):
  if len(errors) > 0:
    return jsonify(
      errors = errors
    )
  else:
    pass

@app.route('/confirm/<email>', methods=['POST'])
def confirm_account(email):
  user = User.query.filter_by(email=email).first()
  user.confirmed = True
  db.session.commit()
  return jsonify(
    email = user.email,
    confirmed = user.confirmed,
    message = f'Account for {user.email} has been activated'
  )

@app.route('/profile/<email>')
def profile_view(email):
  user = User.query.filter_by(email=email).first()
  if user == '':
    return jsonify(
      email = email,
      message = f'Account not found for user: {email}'
    )
  else:
    return jsonify(
              id=user.id,
              email=user.email,
              confirmed = user.confirmed,
              first_name=user.first_name,
              middle_name=user.middle_name,
              last_name=user.last_name,
              zip_code=user.zip_code,
              city=user.city,
              county=user.county,
              state=user.state
            )

@app.route('/profile/update/<email>', methods=['POST'])
def profile_update(email):
  user = User.query.filter_by(email=email).first()
  errors = []

  if user == '':
    return jsonify(
      email = email,
      message = f'Account not found for user: {email}'
    )
  else:
      if 'first_name' in request.form:
        if len(request.form['first_name']) < 2:
          errors.append("First name must include atleast 2 characters")
        else:
          user.first_name = request.form['first_name']
      else:
        errors.append("Please include first_name field with request")

      if 'middle_name' in request.form:
          user.middle_name = request.form['middle_name']

      if 'last_name' in request.form:
        if len(request.form['last_name']) < 2:
          errors.append("Last name must include atleast 2 characters")
        else:
          user.last_name = request.form['last_name']
      else:
        errors.append("Please include last_name field with request")

      if 'zip_code' in request.form:
        zip = request.form['zip_code']
        if len(zip) < 5:
          errors.append("Zip must include atleast 5 numbers")
        else:
          user.zip_code = request.form['zip_code']
      else:
        errors.append("Please include zip_code field with request")

      if 'email' in request.form:
        email = request.form['email']
        if len(email) < 5:
          errors.append("Email prefix must include atleast 5 characters")
        elif not EMAIL_REGEX.match(email):
          errors.append("Invalid Email Address format")
        else:
          return_res_with_errors(errors)
      else:
        errors.append("Please include email field with request")
        return_res_with_errors(errors)

      #retrieve geo data for user
      geo_data = get_geo_data(user.zip_code)

      if geo_data["city"]:
        user.city = geo_data["city"]
      if geo_data["county"]:
        user.county = geo_data["county"]
      if geo_data["state"]:
        user.state = geo_data["state"]

      if len(errors) > 0:
        return jsonify(
          errors = errors
      )
      else:

        db.session.commit()

        return jsonify(
          id=user.id,
          email=user.email,
          first_name=user.first_name,
          middle_name=user.middle_name,
          last_name=user.last_name,
          zip_code=user.zip_code,
          city=user.city,
          county=user.county,
          state=user.state
          )

#return all users
@app.route('/users')
def get_users():
  users = User.query.all()
  users_detail = []

  for user in users:
    users_detail.append(
      {
        'id':user.id,
        'email':user.email,
        'first_name':user.first_name,
        'middle_name':user.middle_name,
        'last_name':user.last_name,
        'zip_code':user.zip_code,
        'city':user.city,
        'county':user.county,
        'state':user.state
      }
    )

  return jsonify(
    users = users_detail
  )

def get_geo_data(zip_code):
  geo_data = json.loads(requests.get('http://api.geonames.org/postalCodeLookupJSON?postalcode=' + zip_code + '&country=US&username=ckearse').content)

  city = geo_data["postalcodes"][0]["placeName"]
  county = geo_data["postalcodes"][0]["adminName2"]
  state = geo_data["postalcodes"][0]["adminCode1"]

  return {'city':city, 'county':county, 'state':state}

if __name__ == "__main__":
  app.run()