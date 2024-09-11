import identity.web
import requests
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

import app_config

__version__ = "0.8.0" 

app = Flask(__name__)
app.config.from_object(app_config)
assert app.config["REDIRECT_PATH"] != "/", "REDIRECT_PATH must not be /"
Session(app)

# This section is needed for url_for("foo", _external=True) to automatically
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.jinja_env.globals.update(Auth=identity.web.Auth)  # Useful in template for B2C
auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)

DB_CONFIG = {
    'host': app.config["DB_HOST"],
    'database': app.config["DB_NAME"],
    'user': app.config["DB_USER"],
    'password': app.config["DB_PASSWORD"],
}

def create_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    return None


def store_user_data(user_data):
    connection = create_db_connection()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        query = """INSERT INTO user_logins 
                   (oid, name, preferred_username, aud, iss, iat, exp, tid, access_time) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (
            user_data.get('oid'),
            user_data.get('name'),
            user_data.get('preferred_username'),
            user_data.get('aud'),
            user_data.get('iss'),
            datetime.fromtimestamp(user_data.get('iat', 0)),
            datetime.fromtimestamp(user_data.get('exp', 0)),
            user_data.get('tid'),
            datetime.now()
        )
        cursor.execute(query, values)
        connection.commit()
    except Error as e:
        print(f"Error while storing user data: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/login")
def login():
    return render_template("login.html", version=__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), 
        prompt="select_account",  
        ))


# error may raise
@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index"))


# log out api
@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index", _external=True)))


# index page 
@app.route("/")
def index():
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template('config_error.html')
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('index.html', user=auth.get_user(), version=__version__)



@app.errorhandler(Exception)
def handle_exception(e):
    # Pass the error message to the error page
    return render_template('error.html', message=str(e)), 500


# call downstream api (for user data storeDB )
@app.route("/call_downstream_api")
def call_downstream_api():
    try:
        token = auth.get_token_for_user(app_config.SCOPE)
        if "error" in token:
            return redirect(url_for("login"))
        
        user_data = auth.get_user()
        print('user_data: ', user_data)
        store_user_data(user_data)
        
        # Use access token to call downstream API
        api_result = requests.get(
            app_config.ENDPOINT,
            headers={'Authorization': 'Bearer ' + token['access_token']},
            timeout=30,
        ).json()

        return render_template('display.html', result=api_result)
    except Exception as e:
        # Log the error for debugging and redirect to the error page
        print(f"Error in API call: {e}")
        return render_template('error.html', message="An error occurred while fetching data.")


if __name__ == "__main__":
    app.run()
