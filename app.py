import stripe
import requests
import json
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
    amount = db.Column(db.Numeric())
    product_id = db.Column(db.String())
    plan_id = db.Column(db.String())
    link = db.Column(db.String())

    def __repr__(self):
        return "(email: {}, password: {}, stage: {})"\
            .format(self.email, self.password, self.stage)


class User:

    def __init__(self, email):
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
        exists = cur.rowcount > 0
        self.new_user = not exists
        if self.new_user:
            self.email = email
            self.password = None
            self.stage = None
            self.twitter_handle = None
            self.account_id = None
            self.amount = 0
            self.product_id = None
            self.plan_id = None
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
                    (email, password, stage, twitter_handle, account_id, amount, product_id, plan_id, link)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [self.email, self.password, self.stage, self.twitter_handle,
                 self.account_id, self.amount, self.product_id, self.plan_id, self.link]
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
                    amount = %s,
                    product_id = %s,
                    plan_id = %s,
                    link = %s
                WHERE
                    email = %s    
                """,
                [self.email, self.password, self.stage, self.twitter_handle,
                 self.account_id, self.amount, self.product_id, self.plan_id, self.link, self.email]
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
        self.amount = user['amount']
        self.product_id = user['product_id']
        self.plan_id = user['plan_id']
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
app.secret_key = '_5#y2L"F4Q8z/'


@login_manager.user_loader
def load_user(email):
    user = User(str(email))
    if user.new_user:
        return None
    return user


@app.route('/')
def root():
    # Check if the user is already logged in and take it to its stage
    return "Welcome to my project!"


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in and take it to its stage
    if current_user.is_authenticated:
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
    if current_user.is_authenticated:
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Save the user
        user = User(email)
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
    error = None
    # Check the user is at the correct stage
    if current_user.stage != 'express_account':
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    if request.method == 'POST':
        client_id = 'ca_E3RUt1fryGahQgpUOMD7eKKyObggpknk'
        # TODO: submit this redirect uri to Stripe
        redirect_uri = request.base_url
        # Build express link
        link = 'https://connect.stripe.com/express/oauth/authorize?' \
               'redirect_uri={}&' \
               'client_id={}&' \
               'state=12345'\
            .format(redirect_uri, client_id)
        return redirect(link)
    if 'code' in request.args:
        authorization_code = request.args.get('code')
        # Use the code to make a post request to the token endpoint to complete the
        # connection and fetch the user's account ID
        url = 'https://connect.stripe.com/oauth/token'
        payload = {
            'client_secret': stripe_keys['secret_key'],
            'code': authorization_code,
            'grant_type': 'authorization_code'
        }
        response = requests.post(url, data=payload)
        account = json.loads(response.content)
        # Save the user's express account information
        current_user.account_id = account['stripe_user_id']
        # Update the user's stage to subscription setup
        current_user.stage = 'subscription_setup'
        current_user.commit()
        return redirect(url_for('subscription_setup'))
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
        current_user.amount = int(amount)
        # Update the user's stage to subscription link
        current_user.stage = 'subscription_link'
        # Setup the product and the plan
        product = stripe.Product.create(
            name='PTF product name',
            type='service',
            stripe_account=current_user.account_id
        )
        current_user.product_id = product['id']
        plan = stripe.Plan.create(
            currency='usd',
            interval='month',
            product=current_user.product_id,
            nickname='Monthly Plan',
            amount=current_user.amount*100,
            stripe_account=current_user.account_id
        )
        current_user.plan_id = plan['id']
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
    # TODO
    link = 'new checkout link'
    # Save the user's subscription link
    current_user.link = link
    current_user.commit()
    return render_template('subscription_link.html', link=link, error=error)


@app.route('/<handle>', methods=['GET', 'POST'])
def checkout(handle):
    error = None
    # Get user based on handle
    conn = psycopg2.connect(DATABASE_URL, sslmode=SSL_mode)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """
        SELECT 
            *
        FROM 
            test_users
        WHERE
            twitter_handle = %s
        """,
        [handle]
    )
    user = cur.fetchone()
    if not user:
        return "This user does not exist."
    # Convert the database information into a user object
    user = User(user['email'])
    conn.close()
    # Get user's subscription amount
    dollars = user.amount
    cents = dollars * 100
    # Create description for checkout page based on the user
    twitter_handle = user.twitter_handle
    return render_template('checkout.html', key=stripe_keys['publishable_key'],
                           twitter_handle=twitter_handle, dollars=dollars, cents=cents, error=error)


@app.route('/charge', methods=['POST'])
def charge():
    # Amount in cents
    email = request.form['stripeEmail']
    amount = int(request.form['amount'])
    stripe_token = request.form['stripeToken']
    twitter_handle = request.form['twitter_handle']
    conn = psycopg2.connect(DATABASE_URL, sslmode=SSL_mode)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """
        SELECT 
            *
        FROM 
            test_users
        WHERE
            twitter_handle = %s
        """,
        [twitter_handle]
    )
    user = cur.fetchone()
    conn.close()
    if not user:
        return
    user = User(user['email'])
    #TODO: store all customers and their subscription and which accounts they are connected to in a seperate table,
    # they need to be able to cancel their plans
    customer = stripe.Customer.create(
        email=email,
        source=stripe_token,
        stripe_account=user.account_id
    )
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[
            {"plan": user.plan_id},
        ],
        application_fee_percent=10,
        stripe_account=user.account_id
    )
    return "Thank you for paying ${}".format(amount/100)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    error = None
    # Check the user is at the correct stage
    if current_user.stage != 'dashboard':
        # Render function based on the stage
        return redirect(url_for(current_user.stage))
    if request.method == 'POST':
        # Build the express dashboard link
        # (generate the link on demand when the user intends to visit the dashboard)
        account = stripe.Account.retrieve(current_user.account_id)
        response = account.login_links.create()
        link = response['url']
        return redirect(link)
    return render_template('dashboard.html', error=error)


if __name__ == '__main__':
    app.run(debug=True)
