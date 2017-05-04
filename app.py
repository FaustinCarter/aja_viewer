import sqlite3
import flask
import pandas as pd
import matplotlib.pyplot as plt

app = flask.Flask(__name__)


DATABASE = '/Users/fcarter/Desktop/AJA/LogsDB.db'

def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(DATABASE)
    return db

@app.route('/')
def index():
    df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", get_db())
    table_names = df['name'].values.tolist()
    return flask.render_template('index.html', table_names = table_names)

@app.route('/recipe_plots', methods=['GET', 'POST'])
def show_plot():
    table_name = flask.request.form['table_name']
    recipe = flask.request.form['submit_plt']
    base_path = './static/'
    img_name = recipe.replace('', '_')+'.png'

    query = """select * from {} where
            Recipe_Steps like ?""".format(table_name)

    df = pd.read_sql_query(query, get_db(), params=(recipe,))

    ax = plt.gca()
    ax.clear()
    for key, val in df.groupby(('Layer_#', 'Logfile_Path')):
        val.plot(ax=ax, legend=False)

    ax.set_title('Recipe summary for: '+recipe)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Some arbitrary thing')
    fig = plt.gcf()

    fig.set_size_inches(10, 9)
    fig.savefig(base_path+img_name)

    return flask.render_template('show_plots.html',
                                recipe_name = recipe,
                                img_name=img_name)

@app.route('/recipe_frequency', methods=['GET', 'POST'])
def calc_recipe_frequency():
    table_name = flask.request.form['table_name']

    query = """select Recipe_Steps, count(Recipe_Steps) as count from
           (select distinct Recipe_Steps, Job_Name, "Layer_#"
           from {}
           where ("RF#1_Shutter" like "OPEN"
           OR "RF#2_Shutter" like "OPEN"
           OR "DC#1_Shutter" like "OPEN"
           OR "DC#5A_Shutter" like "OPEN"
           OR "DC#5B_Shutter" like "OPEN"
           OR "DC#5C_Shutter" like "OPEN"
           OR "DC#5D_Shutter" like "OPEN")
           AND Recipe_Steps not like "%OFF") as internalquery
           group by Recipe_Steps
           order by count desc
           """.format(table_name)
    df = pd.read_sql_query(query, get_db())

    df_head = df.columns.tolist()
    df_data = df.values.tolist()

    return flask.render_template('recipe_freqs.html',
                                 df_head = df_head,
                                 df_data = df_data,
                                 table_name = table_name)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()
