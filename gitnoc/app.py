import json
import os
from flask import Flask, render_template, redirect, url_for, request
from gitpandas import ProjectDirectory
from redis import Redis
from rq import Queue
from gitnoc.forms.public import SettingsForm, ProfileForm, CreateProfileForm
from gitnoc.services.settings import *
from gitnoc.services.cumulative_blame import *
from gitnoc.services.file_change_rates import *
from gitnoc.services.metrics import *

TITLE = "GitNOC"

scripts = [
    "./js/queue.js",
    "./bower_components/jquery/dist/jquery.min.js",
    "./bower_components/d3/d3.min.js",
    "./bower_components/nvd3/build/nv.d3.min.js",
    "./bower_components/datatables/media/js/jquery.dataTables.min.js",
    "./bower_components/datatables-buttons/js/dataTables.buttons.js"
]

css = [
    "./bower_components/bootstrap/dist/css/bootstrap.min.css",
    "./bower_components/nvd3/build/nv.d3.min.css",
    "./bower_components/datatables/media/css/jquery.dataTables.min.css",
    "./bower_components/datatables-buttons/css/buttons.dataTables.scss",
    "./css/main.css"
]

app = Flask(__name__)
app.secret_key = 'CHANGEME'

directory = str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data'
if not os.path.exists(directory):
    os.makedirs(directory)

q = Queue(connection=Redis())


@app.route('/', methods=["GET"])
def metrics():
    leaderboard = week_leader_board(n=5)
    return render_template('metrics.html', leaderboard=leaderboard, title=TITLE, base_scripts=scripts, css=css)


@app.route('/blame', methods=["GET"])
def blame():
    return render_template('blame.html', title=TITLE, base_scripts=scripts, css=css)


@app.route('/profile', methods=["GET", "POST"])
def profile():
    select_form = ProfileForm(request.form)
    create_form = CreateProfileForm(request.form)

    select_form.profile.choices = get_profiles()

    if select_form.validate_on_submit():
        change_profile(select_form.profile.data)
        return redirect(url_for('settings'))
    elif create_form.validate_on_submit():
        create_profile(create_form.name.data)
        change_profile(create_form.name.data)
        return redirect(url_for('settings'))

    select_form.profile.choices = get_profiles()
    select_form.process()

    return render_template('profile.html', create_form=create_form, select_form=select_form, title=TITLE, base_scripts=scripts, css=css)


@app.route('/settings', methods=["GET", "POST"])
def settings():
    form = SettingsForm(request.form)
    if form.validate_on_submit():
        update_profile(form.project_directory.data, form.extensions.data, form.ignore_dir.data)

    settings = get_settings()
    extensions = settings.get('extensions', None)
    if extensions is not None:
        form.extensions.default = ', '.join(extensions)

    project_dir = settings.get('project_dir', None)
    if project_dir is not None:
        if isinstance(project_dir, list):
            form.project_directory.default = ', '.join(project_dir)
        else:
            form.project_directory.default = project_dir

    ignore_dir = settings.get('ignore_dir', None)
    if ignore_dir is not None:
        form.ignore_dir.default = ', '.join(ignore_dir)

    form.process()

    return render_template('settings.html', form=form, title=TITLE, base_scripts=scripts, css=css)


@app.route('/cumulative_author_blame_data', methods=['GET'])
def cumulative_author_blame_data():
    filename = get_file_prefix() + 'cumulative_author_blame.json'
    try:
        return json.dumps(json.load(open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'r')))
    except FileNotFoundError as e:
        return '{}'


@app.route('/cumulative_author_blame', methods=['GET'])
def cumulative_author_blame():
    q.enqueue(cumulative_blame, 'committer', 'cumulative_author_blame.json', timeout=6000)
    return redirect(url_for('blame'))


@app.route('/cumulative_project_blame_data', methods=['GET'])
def cumulative_project_blame_data():
    filename = get_file_prefix() + 'cumulative_project_blame.json'
    try:
        return json.dumps(json.load(open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'r')))
    except FileNotFoundError as e:
        return '{}'


@app.route('/cumulative_project_blame', methods=['GET'])
def cumulative_project_blame():
    q.enqueue(cumulative_blame, 'project', 'cumulative_project_blame.json', timeout=6000)
    return redirect(url_for('blame'))


@app.route('/risk', methods=['GET', 'POST'])
def risk():
    return render_template('filechangerates.html', title=TITLE, base_scripts=scripts, css=css)


@app.route('/file_change_rates', methods=['GET'])
def file_change_rates():
    output = get_file_change_rates()
    return json.dumps(output)

if __name__ == "__main__":
    app.run(debug=True)
