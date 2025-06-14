from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask import session
from uuid import uuid4
from pathlib import Path
import os
from jinja2 import Environment

# db workflow
from script.db_connection import initialize_database, check_password
from script.db_connection import populate_example_data, Session
from script.db_connection import Login as DBLogin
import script.db_connection 

#cusotm import
from script.renderer import render_all_user_information
from script.renderer import render_view_user_information
from script.renderer import render_edit_user_information
from script.renderer import update_rendered_user_information
from script.renderer import render_test_template
from script.renderer import render_user_information
from script.renderer import render_search_page
from script.renderer import render_search_result


app = Flask(__name__)
app.secret_key = "super secret string"
cwd = Path(os.getcwd())
app.static_folder = cwd/"script"/"static"

if not app.has_static_folder:
    raise ImportError("No static folder found")

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
    # This relies on initialize_database() having been called once at startup.
    if not script.db_connection.engine:
        print("Warning: db_connection.engine not initialized in load_user. This might indicate an issue.")
        initialize_database()

    with Session(script.db_connection.engine) as db_session:
        db_login_entry = db_session.query(DBLogin).filter_by(user_name=user_id).one_or_none()
        if db_login_entry:
            return User(username=db_login_entry.user_name)
    return None

# Simple HTML form template
login_template_html = '''
<!doctype html>
<title>Login</title>
<h2>Login Page</h2>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul class=flashes>
    {% for message in messages %}
      <li style="color:red;">{{ message }}</li>
    {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
<form method="POST">
    Username: <input type="text" name="username" required><br><br>
    Password: <input type="password" name="password" required><br><br>
    <input type="submit" value="Login">
</form>
<p><a href="{{ url_for('dashboard') }}">Go to Dashboard</a></p>
'''

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

    return render_template_string(login_template_html)


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

@app.route("/test_endpoint")
def test():


    return render_test_template()

def moccasin_main():
    initialize_database()
    populate_example_data()

    app.run(debug=True, 
            threaded=False, 
            processes = 4,
            host='0.0.0.0',
            port=5000
    )


if __name__=="__main__":
    moccasin_main()