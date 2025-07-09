from flask import Flask, render_template_string, request, redirect, url_for, flash, render_template, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_admin import Admin, helpers
from flask import session
from uuid import uuid4
from pathlib import Path
import os
from jinja2 import Environment
from sqlalchemy.orm import DeclarativeBase
import pandas as pd

from script import roles

# db workflow
from script.db_connection import initialize_database, check_password
from script.db_connection import populate_example_data, Session
from script.db_connection import Login as DBLogin
from script.db_connection import HealthcareRecord, Role
from script.db_connection import add_user
from script.db_connection import get_system_wide_id_and_role
import script.db_connection 

#cusotm import
from script.renderer import render_add_user_form
from script.renderer import render_view_user_information
from script.renderer import render_edit_user_information
from script.renderer import update_rendered_user_information
from script.renderer import render_test_template
from script.renderer import render_user_information
from script.renderer import render_search_page
from script.renderer import render_search_result
from script.renderer import render_added_user
from script.renderer import render_view_all_user
from script.renderer import render_user_table
from script.renderer import render_logs_table
from script.renderer import render_change_password_form 
from script.renderer import render_change_password_result
from script.renderer import render_login_page
from script.renderer import render_permission_denied

app = Flask(__name__, template_folder="script/templates")
app.secret_key = "super secret string"
app.config['SQLALCHEMY_DATABASE_URI']="postgresql://postgres:postgres@localhost:5432/sampledb"
app.config["root_path"]=os.getcwd()
cwd = Path(os.getcwd())
app.static_folder = cwd/"script"/"static"


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # The view to redirect to when login is required

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, username):
        self.id = username # Flask-Login uses this as the user identifier

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database given their ID (username in this case)."""
    # Ensure the database engine is initialized.
    # This relies on initialize_database() having been called at startup (e.g., in moccasin_main).
    if not script.db_connection.engine:
        print("CRITICAL WARNING: db_connection.engine not initialized in load_user. Attempting to initialize now.")
        script.db_connection.initialize_database() # Explicitly call the function from db_connection
        if not script.db_connection.engine:
            raise RuntimeError("Failed to initialize database engine even after explicit call in load_user.")

    with Session(script.db_connection.engine) as db_session:
        db_login_entry = db_session.query(DBLogin).filter_by(user_name=user_id).one_or_none()
        if db_login_entry:
            return User(username=db_login_entry.user_name)
    return None

# Simple HTML form template

@app.route('/login', methods=['GET', 'POST']) 
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Requires db_connection.engine to be initialized.
    
        if check_password(username, password):
            user_obj = User(username=username)
            login_user(user_obj)
            flash('Logged in successfully!')
            return redirect(request.args.get('next') or url_for('dashboard'))
        else:
            flash('Invalid username or password.')
    return render_login_page() 

@app.route("/permission_error")
def permission_error():
    return render_permission_denied()

@app.route("/admin")
@login_required
def load_admin_page():

    if not check_is_admin(current_user.id): 
        return redirect(url_for("permission_error"))
    
    return render_view_all_user(current_user.id)
        

def check_is_admin(username) -> bool:
    try:
        out = get_system_wide_id_and_role(username)
        if out:
            if out[1] == roles.ADMIN:
                return True
    except Exception as e:
        print("Error while getting role:", repr(e))
    return False
    
@app.route("/admin/user_table")
@login_required
def load_user_table():
    if not check_is_admin(current_user.id):
        return redirect(url_for("permission_error"))
    
    try:
        return render_user_table(current_user.id)
    except Exception as e:
        print(e)

@app.route("/admin/add_user", methods = ["POST","GET"])
@login_required
def add_user():
    if not check_is_admin(current_user.id):
        return redirect(url_for("permission_error"))

    if request.method == "GET":
        return render_add_user_form()
    if request.method == "POST":
        try:
            result = render_added_user(current_user.id, request=request)
            response = make_response(result)
            response.headers['HX-Trigger'] = 'reload-user-table'
            return response
        except Exception as e:
            raise e

@app.route("/admin/logs")
@login_required 
def load_logs_table():
    if not check_is_admin(current_user.id):
        return redirect(url_for("permission_error"))
    
    return render_logs_table(current_user.id)

@app.route('/user_information', methods=["GET"])
@login_required 
def get_all_user_information():
    return render_user_information(current_user.id)


@app.route('/user_information/<systemwide_id>', methods=["GET"])
@login_required 
def get_individual_user_information(systemwide_id):
    return render_view_user_information(requestee_id=current_user.id,
                                        system_wide_id=systemwide_id)

@app.route('/edit_user_information/basic/<systemwide_id>', methods=["GET","POST"])
@login_required 
def edit_individual_user_information(systemwide_id):
    if request.method == "GET":  
        return render_edit_user_information(
            requestee_id=current_user.id,
            system_wide_id=systemwide_id)
    
    if request.method == "POST":
        patient_name = request.form.get("full_name")
        address = request.form.get("address")
        dictionary = {"full_name": patient_name,
                      "address":address}
        print("information -------\n",dictionary)
        return update_rendered_user_information(requestee_username=current_user.id,
        system_wide_id=systemwide_id,
        record_data=dictionary)
    return "Error. Endpoint doesn't accept this request method."

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if current_user.is_authenticated:
        if check_is_admin(current_user.id):
            return redirect(url_for('load_admin_page'))
        return redirect(url_for('get_all_user_information'))#Filler: should redirect to individual user information once we the test data anymore
    else:
        return redirect(url_for('login'))

@app.route("/search", methods=["GET","POST"])
@login_required
def search():
    if request.method == "GET":
        return render_search_page(current_user.id)
    if request.method == "POST":
        query_phrase = request.form.get("search")
        if query_phrase:
            return render_search_result(current_user.id, query_phrase)
        else:
            return "No search phrase found"

@app.route("/change_password/<systemwide_id>", methods=["GET","POST"])
def change_password(systemwide_id):

    if request.method == "GET":
        return render_change_password_form(systemwide_id)
    if request.method == "POST":
        new_password = request.form.get("new_password")
        print("Post request -----------", request.form)
        if new_password:
            return render_change_password_result(
                        requestee_username=current_user.id,
                        systemwide_id=systemwide_id,
                        new_password=new_password)

def moccasin_main():
    initialize_database()
    populate_example_data()

    app.run(debug=True, 
            threaded=True,
            host='0.0.0.0',
            port=8500
    )


if __name__=="__main__":
    moccasin_main()