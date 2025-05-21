from flask import Flask, render_template_string, request, redirect, url_for
import flask_login
from flask import session
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "super secret string"

login_manager = flask_login.LoginManager()

login_manager.init_app()

# Simple HTML form template
form_html = '''
<!doctype html>
<title>Login</title>
<h2>Login Page</h2>
<form method="POST">
    Username: <input type="text" name="username" required><br><br>
    Password: <input type="password" name="password" required><br><br>
    <input type="submit" value="Login">
</form>
{% if message %}
<p style="color:red;">{{ message }}</p>
{% endif %}
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple check (you can replace this with a real check)
        if username == 'admin' and password == 'secret':
            session["id"] = uuid4()

            return f"<h2>Welcome, {username}!</h2>"
        
        else:
            message = 'Invalid username or password'

    return render_template_string(form_html, message=message)

def moccasin_main():
    app.run(debug=True)