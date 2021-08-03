
import os
from settings import *

import subprocess
try:
    import winreg as _winreg
except ImportError:  # Python 2
    import _winreg


from collections import OrderedDict

def format_df( df, *args, **kwargs):
    return '\n\t' + df.to_string().replace('\n', '\n\t')

def shell(command,verbose=False,timeout=1200):
    try:
        output,cmd_err = subprocess.Popen(command, stderr=subprocess.PIPE,stdout=subprocess.PIPE, universal_newlines=True).communicate()
        #lg.debug("the commandline is {}".format(output.args))
        #output.wait(timeout)
        #output, cmd_err = output
        output=output
        if verbose:
            print(output)
            print(cmd_err)
        else:
            lg.info(output)
            lg.error(cmd_err)
    except subprocess.CalledProcessError as e:
        output = str(e.output)
        #lg.debug("the commandline is {}".format(output.args))

        lg.error(e.stderr)
    lg.debug(output)
    return output

def as_temp_path(filepath):
    dirname, basename = os.path.split(filepath)
    return os.path.join(dirname,'temp-'+basename)

def yes_or_no(question, default="no"):
    """Ask a yes/no question and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes", "no", or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '{}}'".format(default))

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

# for reading configparser with duplucate section name
class multidict(OrderedDict):
    _unique = 0  # class variable

    def __setitem__(self, key, val):
        if isinstance(val, dict):
            self._unique += 1
            key += ':' * self._unique
        OrderedDict.__setitem__(self, key, val)

def winreg_subvalues(key):
    i = 0
    ks = []
    while True:
        try:
            subkey = _winreg.EnumValue(key, i)
            ks.append(subkey)
            i += 1
        except WindowsError as e:
            break
    return ks

def winreg_traverse_registry_tree(hkey, keypath, tabs=0):
    key = _winreg.OpenKey(hkey, keypath, 0, _winreg.KEY_READ)
    ks = winreg_subvalues(key)
    for subkeyname in ks:
        lg.debug('\t' * tabs + subkeyname[0] + ' ' + subkeyname[1])
        subkeypath = "%s\\%s" % (keypath, subkeyname)
    return ks