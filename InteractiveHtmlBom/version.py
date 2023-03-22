# Update this when new version is tagged.
import os
import subprocess


LAST_TAG = 'v2.6.0'


def _get_git_version():
    plugin_path = os.path.realpath(os.path.dirname(__file__))
    try:
        git_version = subprocess.check_output(
            ['git', 'describe', '--tags', '--abbrev=4', '--dirty=-*'],
            stderr=subprocess.DEVNULL,
            cwd=plugin_path)
        if isinstance(git_version, bytes):
            return git_version.decode('utf-8').rstrip()
        else:
            return git_version.rstrip()
    except subprocess.CalledProcessError:
        # print('Git version check failed: ' + str(e))
        pass
    except Exception:
        # print('Git process cannot be launched: ' + str(e))
        pass
    return None


version = _get_git_version() or LAST_TAG
