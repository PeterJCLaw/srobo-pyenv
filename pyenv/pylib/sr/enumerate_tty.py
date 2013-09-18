import os

class RejectError(Exception):
    pass

REJECT = object()

def find_devices(matcher):
    for (dir_path, subdir_names, filenames) in os.walk('/sys/devices'):
        if 'subsystem' not in subdir_names:
            continue
        def get_attribute(name, default = REJECT):
            try:
                path = "{0}/{1}".format(dir_path, name)
                with open(path, 'r') as f:
                    source = f.read()
                return source.strip()
            except IOError:
                if default is REJECT:
                    raise RejectError()
                else:
                    return default
        try:
            if matcher(get_attribute):
                # Find the TTY name
                for subdir in subdir_names:
                    subdir_path = '{0}/{1}/tty'.format(dir_path, subdir)
                    try:
                        files = os.listdir(subdir_path)
                    except OSError:
                        continue
                    if len(files) != 1:
                        continue
                    yield '/dev/{0}'.format(files[0])
        except RejectError:
            pass

