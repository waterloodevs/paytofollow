import stripe
import psycopg2
import psycopg2.extras
from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/postgres'

app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SSL_mode = 'allow'

stripe_keys = {
  'secret_key': 'sk_test_xhh6fXf9hXSYkBJxHCGZV1nj',
  'publishable_key': 'pk_test_wRgfUidneeegSgn1jkhpiUQp'
}
stripe.api_key = stripe_keys['secret_key']


class TestUsers(db.Model):
    email = db.Column(db.String(), primary_key=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    stage = db.Column(db.String())
    twitter_handle = db.Column(db.String())
    account_id = db.Column(db.String())

    def __repr__(self):
        return "(email: {}, password: {}, stage: {})".format(self.email, self.password, self.stage)


class User:

    def __init__(self, email=None):
        self.new_user = not email
        if self.new_user:
            self.email = None
            self.password = None
            self.stage = None
            self.twitter_handle = None
            self.account_id = None
        else:
            self._populate_user(email)

    def commit(self):
        conn = psycopg2.connect(DATABASE_URL, sslmode=SSL_mode)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if self.new_user:
            # Insert (if this breaks, then the user already exists)
            cur.execute(
                """
                INSERT INTO test_users
                    (email, password, stage, twitter_handle, account_id)
                VALUES
                    (%s, %s, %s, %s, %s)
                """,
                [self.email, self.password, self.stage, self.twitter_handle, self.account_id]
            )
            # This is to prevent committing twice
            self.new_user = False
        else:
            # Update (if this breaks, then the user does not exist)
            conn = psycopg2.connect(DATABASE_URL, sslmode=SSL_mode)
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                """
                UPDATE test_users
                SET
                    email = %s,
                    password = %s,
                    stage = %s,
                    twitter_handle = %s,
                    account_id = %s
                WHERE
                    email = %s    
                """,
                [self.email, self.password, self.stage, self.twitter_handle, self.account_id, self.email]
            )
        conn.commit()
        conn.close()

    def _populate_user(self, email):
        conn = psycopg2.connect(DATABASE_URL, sslmode=SSL_mode)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """
            SELECT 
                *
            FROM 
                test_users
            WHERE
                email = %s
            """,
            [email]
        )
        user = cur.fetchone()
        self.email = user['email']
        self.password = user['password']
        self.stage = user['stage']
        self.twitter_handle = user['twitter_handle']
        self.account_id = user['account_id']
        conn.close()


@app.route('/')
def root():
    # Check if the user is already logged in and take it to its stage
    return "Welcome to my project!"


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in and take it to its stage
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User(email)
        if user.password == password:
            # Get the user's stage
            stage = user.stage
            # Render function based on the stage
            if stage == 'digital_account':
                return redirect(url_for('digital_account', email=user.email))
            elif stage == 'express_account':
                return redirect(url_for('express_account', email=user.email))
            elif stage == 'subscription_setup':
                return redirect(url_for('subscription_setup', email=user.email))
            elif stage == 'subscription_link':
                return redirect(url_for('subscription_link', email=user.email))
            elif stage == 'dashboard':
                return redirect(url_for('dashboard', email=user.email))
            else:
                error = 'Could not find stage of user'
        else:
            error = 'Incorrect credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if the user is already logged in and take it to its stage
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Save the user
        user = User()
        user.email = email
        user.password = password
        # Update the stage to digital account
        user.stage = 'digital_account'
        user.commit()
        return redirect(url_for('digital_account', email=user.email))
    return render_template('signup.html', error=error)


@app.route('/digital_account', methods=['GET', 'POST'])
def digital_account():
    email = request.args.get('email')
    # Assert user is logged in and at the correct stage
    error = None
    if request.method == 'POST':
        twitter_handle = request.form['twitter_handle']
        user = User(email)
        # Save the user's digital account information
        user.twitter_handle = twitter_handle
        # Update the user's stage to express account
        user.stage = 'express_account'
        user.commit()
        return redirect(url_for('express_account', email=user.email))
    return render_template('digital_account.html', error=error, email=email)


@app.route('/express_account', methods=['GET', 'POST'])
def express_account():
    email = request.args.get('email')
    # Assert user is logged in and at the correct stage
    error = None
    if request.method == 'POST':
        if 'code' in request.args:
            user = User(email)
            authorization_code = request.args.get('code')
            # Use the code to make a post request to the token endpoint to complete the
            # connection and fetch the user's account ID
            account = stripe.Account.retrieve(authorization_code)
            # Save the user's express account information
            user.account_id = account['stripe_user_id']
            # Update the user's stage to subscription setup
            user.stage = 'subscription_setup'
            user.commit()
            return redirect(url_for('subscription_setup', email=user.email))
        else:
            CLIENT_ID = 'ca_E3RUt1fryGahQgpUOMD7eKKyObggpknk'
            redirect_uri = request.base_url
            # Build express link
            link = 'https://connect.stripe.com/express/oauth/authorize?redirect_uri={}&client_id={}'\
                .format(redirect_uri, CLIENT_ID)
            return redirect(link)
    return render_template('express_account.html', error=error, email=email)


@app.route('/subscription_setup', methods=['GET', 'POST'])
def subscription_setup():
    email = request.args.get('email')
    # Assert user is logged in and at the correct stage
    error = None
    if request.method == 'POST':
        user = User(email)
        amount = request.form['amount']
        # Save the user's subscription settings
        user.amount = amount
        # Update the user's stage to subscription link
        user.stage = 'subscription_setup'
        user.commit()
        return redirect(url_for('subscription_link', email=user.email))
    return render_template('subscription_setup.html', error=error, email=email)


@app.route('/subscription_link', methods=['GET', 'POST'])
def subscription_link():
    email = request.args.get('email')
    # Assert user is logged in and at the correct stage
    error = None
    user = User(email)
    if request.method == 'POST':
        # Update the user's stage to dashboard
        user.stage = 'dashboard'
        user.commit()
        return redirect(url_for('dashboard', email=user.email))
    # Create the subscription link
    link = 'new checkout link'
    # Save the user's subscription link
    user.link = link
    user.commit()
    return render_template('subscription_link.html', link=link, error=error, email=email)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    email = request.args.get('email')
    # Assert user is logged in and at the correct stage
    # Build the express dashboard link
    # return redirect(link)
    return 'Email: {}. You made it to the dashboard!'.format(email)


if __name__ == '__main__':
    app.run(debug=True)
