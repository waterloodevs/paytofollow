import stripe
import psycopg2
import psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from flask_login import LoginManager, current_user, \
    login_user, logout_user, login_required, UserMixin

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
    link = db.Column(db.String())

    def __repr__(self):
        return "(email: {}, password: {}, stage: {})"\
            .format(self.email, self.password, self.stage)


class User:

    def __init__(self, email=None):
        self.new_user = not email
        if self.new_user:
            self.email = None
            self.password = None
            self.stage = None
            self.twitter_handle = None
            self.account_id = None
            self.link = None
            self.is_authenticated = True
            self.is_active = True
            self.is_anonymous = False
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
                    (email, password, stage, twitter_handle, account_id, link)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                """,
                [self.email, self.password, self.stage,
                 self.twitter_handle, self.account_id, self.link]
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
                    account_id = %s,
                    link = %s
                WHERE
                    email = %s    
                """,
                [self.email, self.password, self.stage, self.twitter_handle,
                 self.account_id, self.link, self.email]
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
        self.link = user['link']
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        conn.close()

    def get_id(self):
        return unicode(self.email)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(email):
    return User(str(email))


@app.route('/')
def root():
    # Check if the user is already logged in and take it to its stage
    return "Welcome to my project!"


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in and take it to its stage
    if current_user:
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User(email)
        if user.password == password:
            login_user(user)
            # Get the user's stage
            stage = user.stage
            # Render function based on the stage
            return redirect(url_for(stage))
        else:
            error = 'Incorrect credentials. Please try again.'
    return render_template('login.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if the user is already logged in and take it to its stage
    if current_user:
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
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
        login_user(user)
        return redirect(url_for('digital_account'))
    return render_template('signup.html', error=error)


@app.route("/logout", methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('root'))


@app.route('/digital_account', methods=['GET', 'POST'])
@login_required
def digital_account():
    # Check the user is at the correct stage
    if current_user.stage != 'digital_account':
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    error = None
    if request.method == 'POST':
        twitter_handle = request.form['twitter_handle']
        # Save the user's digital account information
        current_user.twitter_handle = twitter_handle
        # Update the user's stage to express account
        current_user.stage = 'express_account'
        current_user.commit()
        return redirect(url_for('express_account'))
    return render_template('digital_account.html', error=error)


@app.route('/express_account', methods=['GET', 'POST'])
@login_required
def express_account():
    # Check the user is at the correct stage
    if current_user.stage != 'express_account':
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    error = None
    if request.method == 'POST':
        if 'code' in request.args:
            authorization_code = request.args.get('code')
            # Use the code to make a post request to the token endpoint to complete the
            # connection and fetch the user's account ID
            account = stripe.Account.retrieve(authorization_code)
            # Save the user's express account information
            current_user.account_id = account['stripe_user_id']
            # Update the user's stage to subscription setup
            current_user.stage = 'subscription_setup'
            current_user.commit()
            return redirect(url_for('subscription_setup'))
        else:
            client_id = 'ca_E3RUt1fryGahQgpUOMD7eKKyObggpknk'
            # TODO: submit this redirect uri to Stripe
            redirect_uri = request.base_url
            # Build express link
            link = 'https://connect.stripe.com/express/oauth/authorize?' \
                   'redirect_uri={}&' \
                   'client_id={}'\
                .format(redirect_uri, client_id)
            return redirect(link)
    return render_template('express_account.html', error=error)


@app.route('/subscription_setup', methods=['GET', 'POST'])
@login_required
def subscription_setup():
    # Check the user is at the correct stage
    if current_user.stage != 'subscription_setup':
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    error = None
    if request.method == 'POST':
        amount = request.form['amount']
        # Save the user's subscription settings
        current_user.amount = amount
        # Update the user's stage to subscription link
        current_user.stage = 'subscription_setup'
        current_user.commit()
        return redirect(url_for('subscription_link'))
    return render_template('subscription_setup.html', error=error)


@app.route('/subscription_link', methods=['GET', 'POST'])
@login_required
def subscription_link():
    # Check the user is at the correct stage
    if current_user.stage != 'subscription_link':
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    error = None
    if request.method == 'POST':
        # Update the user's stage to dashboard
        current_user.stage = 'dashboard'
        current_user.commit()
        return redirect(url_for('dashboard'))
    # Create the subscription link
    link = 'new checkout link'
    # Save the user's subscription link
    current_user.link = link
    current_user.commit()
    return render_template('subscription_link.html', link=link, error=error)


@app.route('/subscription_link/<handle>', methods=['GET', 'POST'])
def checkout(handle):
    error = None
    # Get user based on handle or email or whatever
    user = ''
    # Get user's subscription amount
    # Create description for checkout page based on the user
    description = ''
    return render_template('checkout.html', key=stripe_keys['publishable_key'],
                           description=description, amount=user.amount, error=error)


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Check the user is at the correct stage
    if current_user.stage != 'dashboard':
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    # Build the express dashboard link
    # (generate the link on demand when the user intends to visit the dashboard)
    account = stripe.Account.retrieve(current_user.account_id)
    response = account.login_links.create()
    link = response['url']
    return 'Email: {}. You made it to our dashboard!'.format(current_user.email)


if __name__ == '__main__':
    app.run(debug=True)
