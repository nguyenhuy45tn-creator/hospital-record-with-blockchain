import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from flask import url_for

env = Environment(
    loader=FileSystemLoader("script/templates/"),
    autoescape=select_autoescape()
)

def render_all_user_information(user_id: list = None) -> str:
    if user_id is None:
        # fetch all user
        user_information_table = pd.read_csv("script/mock-data/test_data.csv")
    template = env.get_template('user_information_table.html.jinja')
    return template.render(df=user_information_table,
                           url_for=url_for)

if __name__=="__main__":
    with open('test.html','w') as file:
        file.write(render_all_user_information())