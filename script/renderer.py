import pandas as pd
from eth_account import Account
from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask import url_for, jsonify, Request, get_flashed_messages
from flask import redirect
from wtforms import Form, StringField, PasswordField, SelectField, validators
import json
import boa

from script.db_connection import get_all_users
from script.db_connection import get_single_user
from script.db_connection import update_patient_basic_data
from script.db_connection import get_system_wide_id_and_role
from script.db_connection import check_search_access
from script.db_connection import search_users
from script.db_connection import add_user
from script.db_connection import get_all_roles
from script.db_connection import change_password

from script.contract_logger import logged, contract_logger, conn

from script import roles
from web3 import Web3
#logger
from script.contract_logger import logged

env = Environment(
    loader=FileSystemLoader("script/templates/"),
    autoescape=select_autoescape()
)

#mock dataset
# user_information_table = pd.read_csv("script/mock-data/test_data.csv")

def dummy(*args, **kwargs):
    #a dummy function that do nothing so it doesn't messup url template
    pass

# @logged()
# def render_all_user_information(requestee_username, url_for = None) -> str:
    
#     users = get_all_users(requestee_username=requestee_username)
#     users = pd.DataFrame([user.to_dict() for user in users])
#     template = env.get_template('user_information/view_all_user_information_table.html')
#     try:
#         return template.render(df=users,
#                            url_for=url_for)
#     except Exception as e:
#         return template.render(df=users,
#                                url_for=dummy)


@logged()
def render_view_user_information(requestee_id, system_wide_id) -> str:

    user = get_single_user(requestee_username=requestee_id,
                         user_system_wide_identifier=system_wide_id)
    table = pd.DataFrame([user.to_dict(),])
    template = env.get_template('user_information/view_user_info.html')

    return template.render(df=table,
                           full_name = str(user.full_name),
                           username=str(user.user_name),
                           user_id=str(user.user_id),
                           sys_wide_id=str(user.system_wide_identifier),
                           address=str(user.address),
                           url_for=url_for)
@logged()
def render_edit_user_information(requestee_id, system_wide_id) -> str:
    user = get_single_user(requestee_username=requestee_id,
                         user_system_wide_identifier=system_wide_id)
    table = pd.DataFrame([user.to_dict(),])
    template = env.get_template("user_information/edit_user_information.html")
    return template.render(df=table,
                           full_name = str(user.full_name),
                           username=str(user.user_name),
                           user_id=str(user.user_id),
                           sys_wide_id=str(user.system_wide_identifier),
                           address=str(user.address),
                           url_for=url_for)
@logged()
def render_login_page():
    template = env.get_template("login_page.html")
    return template.render(url_for=url_for, get_flashed_messages=get_flashed_messages)

def render_change_password_form(systemwide_id):
    template = env.get_template("user_information/change_password_form.html")
    return template.render(sys_wide_id=systemwide_id)

@logged()
def render_change_password_result(requestee_username,systemwide_id, new_password):
    result = "Successfully changed the password"
    _,role = get_system_wide_id_and_role(requestee_username=requestee_username)
    try:
        change_password(
            requestee_username=requestee_username, 
            target_sys_id=systemwide_id, 
            new_password=new_password)
    except Exception as e:
        result = "Fail changing the password"
        print(repr(e))
    template = env.get_template("user_information/change_password_status.html")
    return template.render(status=result, render=(role != roles.ADMIN))

    
@logged()
def render_search_page(requestee_id) -> str:
    try:
        check_search_access(requestee_id)
    except PermissionError:
        return "Error \n" + "you don't have the right to access"
    template = env.get_template("search-page.html")
    return template.render(url_for=url_for)


@logged()
def update_rendered_user_information(requestee_username,
                                    system_wide_id,
                                    record_data) -> str:

    update_patient_basic_data(
        requestee_username=requestee_username,
        sys_wide_id= system_wide_id,
        record_data= record_data)
    return render_view_user_information(requestee_id=requestee_username,
                                        system_wide_id=system_wide_id)

@logged()
def render_search_result(requestee_usernam, search_phrase):
    search_result:list[str] = search_users(
        requestee_username=requestee_usernam,
        search_phrase=search_phrase)
    template = env.get_template("search/search-result.html")
    return template.render(result=search_result)


def render_test_template():
    template = env.get_template("index.html")
    return template.render(
                           url_for=url_for)

@logged()
def render_user_table(requestee_username):
    def get_edit_link(row: pd.DataFrame):
        template = env.get_template("admin_components/edit_cell_user_table.html")
        return template.render(sys_id=row["system_wide_identifier"])
    
    try:
        content = get_all_users(requestee_username=requestee_username)
        table = pd.DataFrame(content).set_index("user_id")
        table[" "] = table.apply(get_edit_link, axis=1)
        content = table.style.set_table_attributes('class="table table-hover" hx-trigger="reload-user-table from:body" hx-get="/admin/user_table"').to_html()
        return content
    except Exception as e:
        print(repr(e))

@logged()
def render_permission_denied():
    template = env.get_template("permission_error.html")
    return template.render(url_for=url_for)

@logged()
def render_view_all_user(requestee_username):
    template = env.get_template("admin_components/admin_user.html")
    return template.render(url_for=url_for)

class CreateUserForm(Form):
    full_name = StringField(label="Full Name", 
                            validators=[
                                validators.InputRequired(), 
                                validators.Regexp(regex="^[A-Za-z0-9_. ]+$")
                            ])
    address = StringField(label="Address", 
                            validators=[
                                validators.InputRequired(), 
                                validators.Regexp(regex="^[A-Za-z0-9_. ]+$")
                            ])
    hospital_designation = StringField(label="Designated hospital", 
                                validators=[
                                    validators.InputRequired(), 
                                    validators.Regexp(regex="^[A-Za-z0-9_. ]+$")
                                ],
                                default="This hosital")
    role_for_new_user = SelectField(label="Roles", choices=get_all_roles())

@logged()
def render_logs_table(requestee_username):
    
    
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
    if not w3.is_connected():
        raise ConnectionAbortedError("No provider found")
    
    weth_contract = w3.eth.contract(
        address=contract_logger.address, 
        abi=contract_logger.abi)
    
    logs = weth_contract.events.AppLog().get_logs(from_block=w3.eth.block_number)

    if conn is not None:
        total_cached_rec = conn.execute("""
            SELECT log_mss
            FROM cached_logs
        """).fetchall()

    print(f"logs is {logs[-1]}")
    if len(total_cached_rec) == logs[0].args.value:
        logs = [json.loads(mss[0]) for mss in total_cached_rec]
    else:
        with boa.fork("http://127.0.0.1:8545", allow_dirty=True):
            log_length = contract_logger.get_length() 
            logs = []
            for i in range(1, log_length):
                logs.append(json.loads(contract_logger.log_db(i)))

    table=pd.DataFrame(logs).sort_values("ts", ascending=False)
    return table.style.set_table_attributes('class="table table-hover" hx-trigger="every 3s" hx-get="/admin/logs"').to_html()

def render_added_user(requestee_username, request: Request):
    form = CreateUserForm(request.form)
    if request.method == 'POST' and form.validate():
        username, password_plain = add_user(requestee_username=requestee_username,
                                            full_name=form.full_name.data,
                                            address=form.address.data,
                                            hospital_designation=form.hospital_designation.data,
                                            role_for_new_user=form.role_for_new_user.data)
    template = env.get_template("admin_components/new_user_account.html")
    return template.render(new_username = username, 
                           new_password=password_plain,
                           form=form)

def render_add_user_form():
    form = CreateUserForm()
    template = env.get_template("admin_components/add_user_form.html")
    return template.render(form=form)

@logged()
def render_user_information(requestee_username: str):

    sys_id, role = get_system_wide_id_and_role(requestee_username=requestee_username)

    if role == roles.PATIENT:
        return render_view_user_information(requestee_id=requestee_username,
                                            system_wide_id=sys_id)
    elif role in [roles.ADMIN, roles.DOCTOR, roles.NURSE]:
        return redirect(url_for('search'))
    else:
        raise PermissionError()

if __name__=="__main__":
    with open('test.html','w') as file:
        file.write(render_view_user_information("xyz9999"))