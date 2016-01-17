from flask import Flask, render_template, redirect, url_for, request
from redis import Redis
from rq import Queue
from flask_cache import Cache

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
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

directory = str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data'
if not os.path.exists(directory):
    os.makedirs(directory)

q = Queue(connection=Redis())


def render_wrapper(template, **kwargs):
    current_profile = get_settings()['profile_name']
    return render_template(template, title=TITLE, base_scripts=scripts, css=css, profile_name=current_profile, **kwargs)


@app.route('/', methods=["GET"])
def metrics():
    leaderboard = week_leader_board(n=5)
    return render_wrapper('metrics.html', leaderboard=leaderboard)


@app.route('/blame', methods=["GET"])
def blame():
    return render_wrapper('blame.html')


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
    select_form.profile.default = get_settings()['profile_name']
    select_form.process()

    return render_wrapper('profile.html', create_form=create_form, select_form=select_form)


@app.route('/settings', methods=["GET", "POST"])
def settings():
    form = SettingsForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        update_profile(form.project_directory.data, form.extensions.data, form.ignore_dir.data)

    settings = get_settings()
    extensions = settings.get('extensions', None)
    project_dir = settings.get('project_dir', None)
    ignore_dir = settings.get('ignore_dir', None)

    if project_dir is not None:
        if isinstance(project_dir, list):
            pdv = ','.join(project_dir)
        else:
            pdv = project_dir
    else:
        pdv = ''

    if extensions is not None:
        if isinstance(project_dir, list):
            ext = ','.join(extensions)
        else:
            ext = extensions
    else:
        ext = ''

    if ignore_dir is not None:
        if isinstance(project_dir, list):
            ign = ','.join(ignore_dir)
        else:
            ign = ignore_dir
    else:
        ign = ''

    return render_wrapper('settings.html', form=form, project_directory_values=pdv, ignore_dir_values=ign, extensions_values=ext)


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
    return render_wrapper('filechangerates.html')


@app.route('/file_change_rates', methods=['GET'])
@cache.cached(timeout=300)
def file_change_rates():
    output = get_file_change_rates()
    return json.dumps(output)


@app.route('/punchcard_data', methods=['GET'])
@cache.cached(timeout=300)
def punchchard_data():
    output = get_punchcard()
    return str(output)

if __name__ == "__main__":
    app.run(debug=True)
