# Update this when new version is tagged.
LAST_TAG = 'v2.3'

import os
plugin_path = os.path.realpath(os.path.dirname(__file__))
plugin_path if not os.path.islink(plugin_path) else os.readlink(plugin_path)

def _get_git_version():
    import os, subprocess
    try:
        git_version = subprocess.check_output(
                ['git', 'describe', '--tags', '--abbrev=4', '--dirty=-*'],
                cwd=plugin_path)
        return git_version.decode('utf-8') if isinstance(git_version, bytes) else git_version
    except subprocess.CalledProcessError as e:
        print('Git version check failed: ' + str(e))
    except Exception as e:
        print('Git process cannot be launched: ' + str(e))
    return None


version = _get_git_version() or LAST_TAG
