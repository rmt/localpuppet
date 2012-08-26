#!/usr/bin/python
"""
This script will let you run puppet standalone with
support for multiple environments (eg. version'd environments)

It requires a directories of release directories under /etc/puppet/apps
Each top-level release directory requires a manifest.yaml file
which includes the key 'modulepath' with a list of directories
relative to /etc/puppet/src/. These will be added to 
puppet's modulepath.
"""

import sys
import os
import yaml
import shutil
import os.path

APP_MODULE_DIR="/etc/puppet/modules"
DEST_ENC_YAML="/etc/puppet/node.yaml"
INPUT_YAML="/etc/puppet/input.yaml"
PUPPET_MANIFEST="/etc/puppet/manifests/default.pp"
ENC_PATH="/etc/puppet/enc.sh"

def die(msg, exitcode=1):
    print >>sys.stderr, msg
    sys.exit(exitcode)

def get_raw_enc_data(args):
    if args:
        filename = args[0]
    else:
        filename = INPUT_YAML
    return yaml.load(open(filename, "rb"))

def normalise_enc_data(encdata):
    classes = encdata.get("classes", {})
    parameters = encdata.get("parameters", {})
    # ensure each class is a dictionary, and strip None items so
    # that parameter defaults can take effect.
    for key in classes.keys():
        value = classes[key]
        if value is None:
            classes[key] = {}
        elif type(value) == dict:
            # remove None items, so puppet defaults can take effect
            for k,v in value.items():
                if v is None:
                    del value[k]
        else:
            del classes[key]
    # return only classes and parameters
    return {
        "classes": classes,
        "parameters": parameters,
    }

def get_modulepath(module_dir, app_dirs):
    """Verify app_dirs and return the colon-separated module path"""
    assert module_dir and os.path.isdir(module_dir)
    assert app_dirs
    assert len(app_dirs) < 10
    modulepath = []
    for appdir in iter(app_dirs):
        assert not appdir.startswith("/")
        assert ".." not in appdir
        fullpath = os.path.join(module_dir, appdir)
        if not os.path.exists(fullpath):
            die("app_dir {0} does not exist.".format(appdir))
        modulepath.append(fullpath)
    return ":".join(modulepath)

def get_app_dirs(module_dir, app_dir):
    assert not app_dir.startswith("/")
    assert ".." not in app_dir
    dir = os.path.join(module_dir, app_dir)
    if not os.path.isdir(dir):
        die("Directory doesn't exist: {0}".format(dir))
    manifest = os.path.join(dir, "manifest.yaml")
    if not os.path.exists(manifest):
        die("Manifest file doesn't exist: {0}".format(manifest))
    data = yaml.load(open(manifest))
    if "modulepath" in data:
        return [app_dir] + data["modulepath"]
    return []

def main():
    encdata = get_raw_enc_data(sys.argv[1:])
    try:
        app = encdata["app"]
    except KeyError:
        die("ERROR: Input YAML must have an 'app' key")
        sys.exit(1)
    app_dirs = get_app_dirs(APP_MODULE_DIR, app)
    modulepath = get_modulepath(APP_MODULE_DIR, app_dirs)
    with open(DEST_ENC_YAML,"wb") as fd:
        yaml.dump(normalise_enc_data(encdata), fd)
    args = [
        "/usr/bin/puppet",
        "apply",
        "--node_terminus",
        "exec",
        "--external_nodes",
        ENC_PATH,
        "--modulepath",
        modulepath,
        PUPPET_MANIFEST
    ]
    print("# "+' '.join(args))
    os.execv("/usr/bin/puppet", args)

if __name__ == "__main__":
    main()
