import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask import url_for

env = Environment(
    loader=FileSystemLoader("script/templates/"),
    autoescape=select_autoescape()
)

#mock dataset
user_information_table = pd.read_csv("script/mock-data/test_data.csv")

def render_all_user_information() -> str:
    """Renders a Jinja2 template with user information.
     
    It then renders the 'user_information_table.html.jinja' 
    template, passing the user information DataFrame 
    and the `url_for` function to it.

    Args:
        user_id: A list of user IDs to filter the information.
                 Currently, this parameter is not used and all
                 user information is fetched. Defaults to None.

    Returns:
        A string containing the rendered HTML content.
    """

    # fetch all user
    
    template = env.get_template('user_information/view_all_user_information_table.html')
    return template.render(df=user_information_table,
                           url_for=url_for)

def render_view_user_information(user_id: str) -> str:
    """
    User information can only be edited one at a time. Mass editing 
    is diable.
    """
    table = user_information_table[user_information_table["username"] == user_id]
    template = env.get_template("user_information/view_user_info.html")
    return template.render(df=table,
                           user_id=user_id,
                           url_for=url_for)

def render_edit_user_information(user_id: str) -> str:
    """
    User information can only be edited one at a time. Mass editing 
    is diable.
    """
    table = user_information_table[user_information_table["username"] == user_id]
    template = env.get_template("user_information/edit_user_information.html")
    return template.render(user_id=user_id,
                           df=table)

def update_rendered_user_information(username:str, user_information:dict) -> str:
    global user_information_table
    user_selector = user_information_table["username"] == username
    for key in user_information.keys():
        user_information_table.loc[user_selector, key] = user_information[key]
    table = user_information_table[user_information_table["username"] == username]
    print(table)
    return render_view_user_information(user_id=username)

if __name__=="__main__":
    with open('test.html','w') as file:
        file.write(render_view_user_information("xyz9999"))