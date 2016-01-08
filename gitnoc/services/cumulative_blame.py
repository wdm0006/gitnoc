import os
import json
import threading
from gitpandas import ProjectDirectory
from gitnoc.services.services import get_settings, get_file_prefix

__author__ = 'willmcginnis'


def cumulative_blame(by, file_stub):
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)

    repo = ProjectDirectory(working_dir=project_dir)
    print(extensions)
    print(ignore_dir)
    print(by)
    cb = repo.cumulative_blame(branch='master', extensions=extensions, ignore_dir=ignore_dir, by=by, num_datapoints=100, skip=None, limit=None)
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
    filename = get_file_prefix() + file_stub
    json.dump(d3_data, open(str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'w'), indent=4)

    return True


class BlameThread(threading.Thread):
    def __init__(self, by, file_stub):
        super(BlameThread, self).__init__()
        self.daemon = True
        self.__monitor = threading.Event()
        self.__monitor.set()
        self.__has_shutdown = False
        self.by = by
        self.file_stub = file_stub

    def run(self):
        self.startup()
        while self.isRunning():
            self.mainloop()
        self.cleanup()
        self.__has_shutdown = True

    def stop(self):
        self.__monitor.clear()

    def isRunning(self):
        return self.__monitor.isSet()

    def isShutdown(self):
        return self.__has_shutdown

    def mainloop(self):
        cumulative_blame(self.by, self.file_stub)
        self.stop()

    def startup(self):
        pass

    def cleanup(self):
        pass
