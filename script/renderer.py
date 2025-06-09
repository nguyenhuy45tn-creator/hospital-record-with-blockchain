import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask import url_for

from script.db_connection import get_all_users
from script.db_connection import get_single_user
from script.db_connection import update_patient_basic_data
from script.db_connection import get_system_wide_id
from script.db_connection import check_search_access
from script.db_connection import search_users
from flask import redirect, url_for

from script import roles

env = Environment(
    loader=FileSystemLoader("script/templates/"),
    autoescape=select_autoescape()
)

#mock dataset
# user_information_table = pd.read_csv("script/mock-data/test_data.csv")

def dummy(*args, **kwargs):
    #a dummy function that do nothing so it doesn't messup url template
    pass

def render_all_user_information(requestee_username, url_for = None) -> str:
    # """Renders a Jinja2 template with user information.
     
    # It then renders the 'user_information_table.html.jinja' 
    # template, passing the user information DataFrame 
    # and the `url_for` function to it.

    # Args:
    #     user_id: A list of user IDs to filter the information.
    #              Currently, this parameter is not used and all
    #              user information is fetched. Defaults to None.

    # Returns:
    #     A string containing the rendered HTML content.
    # """

    # # fetch all user
    
    users = get_all_users(requestee_username=requestee_username)
    users = pd.DataFrame([user.to_dict() for user in users])
    template = env.get_template('user_information/view_all_user_information_table.html')
    try:
        return template.render(df=users,
                           url_for=url_for)
    except Exception as e:
        return template.render(df=users,
                               url_for=dummy)



def render_view_user_information(requestee_id, system_wide_id) -> str:
    """
    User information can only be edited one at a time. Mass editing 
    is diable.
    """
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

def render_search_page(requestee_id) -> str:
    try:
        check_search_access(requestee_id)
    except PermissionError:
        return "Error \n" + "you don't have the right to access"
    template = env.get_template("search-page.html")
    return template.render(url_for=url_for)


def update_rendered_user_information(requestee_username,
                                    system_wide_id,
                                    record_data) -> str:
    # global user_information_table
    # user_selector = user_information_table["username"] == username
    # for key in user_information.keys():
    #     user_information_table.loc[user_selector, key] = user_information[key]
    # table = user_information_table[user_information_table["username"] == username]


    update_patient_basic_data(
        requestee_username=requestee_username,
        sys_wide_id= system_wide_id,
        record_data= record_data)
    return render_view_user_information(requestee_id=requestee_username,
                                        system_wide_id=system_wide_id)

def render_search_result(requestee_usernam, search_phrase):
    search_result:list[str] = search_users(
        requestee_username=requestee_usernam,
        search_phrase=search_phrase)
    template = env.get_template("search/search-result.html")
    return template.render(results=search_result)

def render_test_template():
    template = env.get_template("index.html")
    return template.render(
                           url_for=url_for)

def render_user_information(requestee_username: str):

    sys_id, role = get_system_wide_id(requestee_username=requestee_username)

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