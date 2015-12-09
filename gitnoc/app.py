from flask import Flask, render_template, redirect, url_for, request
import json
import os
from gitpandas import ProjectDirectory
from gitnoc.forms.public import SettingsForm, ProfileForm, CreateProfileForm

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


def get_settings():
    try:
        bp = str(os.path.dirname(os.path.abspath(__file__)))
        configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
        for config in configs:
            if config.get('current_profile', False):
                return config
        return {}
    except:
        return {}


def get_profiles():
    try:
        bp = str(os.path.dirname(os.path.abspath(__file__)))
        configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
        choices = []
        for config in configs:
            choices.append((config.get('profile_name', ''), config.get('profile_name', '')))
        return choices
    except:
        return []


def get_file_prefix():
    try:
        bp = str(os.path.dirname(os.path.abspath(__file__)))
        configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
        for config in configs:
            if config.get('current_profile', False):
                return config.get('profile_name', '').replace(' ', '_') + '_'
        return ''
    except:
        return ''


def create_profile(profile_name):
    bp = str(os.path.dirname(os.path.abspath(__file__)))
    configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
    configs.append({
        "profile_name": profile_name,
        "current_profile": False,
        "extensions": None,
        "ignore_dir": None,
        "project_dir": None
    })
    json.dump(configs, open(bp + os.sep + 'settings.json', 'w'), indent=4)
    return True


def change_profile(profile_name):
    bp = str(os.path.dirname(os.path.abspath(__file__)))
    configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
    out = []
    for config in configs:
        if config.get('current_profile', True):
            config['current_profile'] = False
        if config.get('profile_name', '') == profile_name:
            config['current_profile'] = True
        out.append(config)
    json.dump(out, open(bp + os.sep + 'settings.json', 'w'), indent=4)
    return True


def update_profile(project_dir, extensions, ignore_dir):
    bp = str(os.path.dirname(os.path.abspath(__file__)))
    configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
    out = []
    for config in configs:
        if config.get('current_profile', False):
            config['project_dir'] = project_dir
            config['extensions'] = extensions
            config['ignore_dir'] = ignore_dir
        out.append(config)
    json.dump(out, open(bp + os.sep + 'settings.json', 'w'), indent=4)
    return True


@app.route('/', methods=["GET"])
def index():
    return render_template('index.html', title=TITLE, base_scripts=scripts, css=css)


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
    return json.dumps(json.load(open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'r')))


@app.route('/cumulative_author_blame', methods=['GET'])
def cumulative_author_blame():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)

    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.cumulative_blame(extensions=extensions, ignore_dir=ignore_dir)
    cb = cb[~cb.index.duplicated()]
    t = json.loads(cb.to_json(orient='columns'))

    d3_data = []
    for committer in t.keys():
        blob = dict()
        blob['key'] = committer
        blob['values'] = []
        for data_point in t[committer].keys():
            blob['values'].append([int(float(data_point)), t[committer][data_point]])
            blob['values'] = sorted(blob['values'], key=lambda x: x[0])
        d3_data.append(blob)

    # dump the data to disk
    filename = get_file_prefix() + 'cumulative_author_blame.json'
    json.dump(d3_data, open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'w'), indent=4)
    return redirect(url_for('index'))


@app.route('/cumulative_project_blame_data', methods=['GET'])
def cumulative_project_blame_data():
    filename = get_file_prefix() + 'cumulative_project_blame.json'
    return json.dumps(json.load(open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'r')))


@app.route('/cumulative_project_blame', methods=['GET'])
def cumulative_project_blame():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)

    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.cumulative_blame(extensions=extensions, ignore_dir=ignore_dir, by='project')
    cb = cb[~cb.index.duplicated()]
    t = json.loads(cb.to_json(orient='columns'))

    d3_data = []
    for committer in t.keys():
        blob = dict()
        blob['key'] = committer
        blob['values'] = []
        for data_point in t[committer].keys():
            blob['values'].append([int(float(data_point)), t[committer][data_point]])
            blob['values'] = sorted(blob['values'], key=lambda x: x[0])
        d3_data.append(blob)

    # dump the data to disk
    filename = get_file_prefix() + 'cumulative_project_blame.json'
    json.dump(d3_data, open(str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'w'), indent=4)
    return redirect(url_for('index'))


@app.route('/risk', methods=['GET', 'POST'])
def risk():
    return render_template('filechangerates.html', title=TITLE, base_scripts=scripts, css=css)


@app.route('/file_change_rates', methods=['GET'])
def file_change_rates():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.file_change_rates(extensions=extensions, ignore_dir=ignore_dir, coverage=True)
    cb.reset_index(level=0, inplace=True)
    data = json.loads(cb.to_json(orient='records'))

    output = {'data': []}
    for blob in data:
        row = [blob.get(x, None) for x in ['index', 'repository', 'unique_committers', 'net_rate_of_change', 'abs_rate_of_change', 'edit_rate', 'total_lines', 'coverage']]
        row = [round(x, 2) if isinstance(x, float) else x for x in row]
        output['data'].append(row)

    return json.dumps(output)

if __name__ == "__main__":
    app.run(debug=True)
