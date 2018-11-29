from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

DATABASE_URL = ''

app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SSL_mode = 'allow'


class User(db.Model):
    __tablename__ = 'Users'
    email = db.Column(db.String(), primary_key=True, nullable=False)
    stage = db.Column(db.String())

    def __repr__(self):
        return "(email: {}, stage: {})".format(self.email, self.stage)


@app.route('/')
def root():
    # Check if the user is already logged in and take it to its stage
    return "Welcome to my project!"


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in and take it to its stage
    error = None
    if request.method == 'POST':
        if successful:
            # Get the user's stage
            # Render function based on the stage
            return redirect(url_for(stage))
        else:
            error = 'Unsuccessful. Please try again.'
    return render_template('login.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if the user is already logged in and take it to its stage
    error = None
    if request.method == 'POST':
        if successful:
            # Save the user
            # Update the stage to digital account
            return redirect(url_for('digital_account'))
        else:
            error = 'Unsuccessful. Please try again.'
    return render_template('signup.html', error=error)


@app.route('/digital_account', methods=['GET', 'POST'])
def digital_account():
    # Asset user is logged in and at the correct stage
    error = None
    if request.method == 'POST':
        if successful:
            # Save the user's digital account information
            # Update the user's stage to express account
            return redirect(url_for('express_account'))
        else:
            error = 'Unsuccessful. Please try again.'
    return render_template('digital_account.html', error=error)


@app.route('/express_account', methods=['GET', 'POST'])
def express_account():
    # Asset user is logged in and at the correct stage
    error = None
    if request.method == 'POST':
        if 'code' in request.args:
            authorization_code = request.args.get('code')
            # Use the code to make a post request to the token endpoint to complete the
            # connection and fetch the user's account ID
            # Save the user's express account information
            # Update the user's stage to subscription setup
            return redirect(url_for('subscription_setup'))
        else:
            CLIENT_ID = ''
            redirect_uri = url_for('express_account')
            # Build express link
            redirect(link)
    return render_template('express_account.html', error=error)


@app.route('/subscription_setup', methods=['GET', 'POST'])
def subscription_setup():
    # Asset user is logged in and at the correct stage
    error = None
    if request.method == 'POST':
        if successful:
            # Save the user's subscription settings
            # Update the user's stage to subscription link
            return redirect(url_for('subscription_link'))
        else:
            error = 'Unsuccessful. Please try again.'
    return render_template('subscription_setup.html', error=error)


@app.route('/subscription_link', methods=['GET', 'POST'])
def subscription_link():
    # Asset user is logged in and at the correct stage
    # Create the subscription link
    # Save the user's subscription link
    error = None
    if request.method == 'POST':
        # Update the user's stage to dashboard
        return redirect(url_for('dashboard'))
    return render_template('subscription_link.html', link=link, error=error)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    # Asset user is logged in and at the correct stage
    # Build the express dashboard link
    return redirect(link)


if __name__ == '__main__':
    app.run(debug=True)
