
import os
from settings import *

import subprocess
try:
    import winreg as _winreg
except ImportError:  # Python 2
    import _winreg


from collections import OrderedDict

# import the necessary packages
from PIL import Image
import imagehash
import argparse
import win32api
import re
import configparser
import logging

logger = logging.getLogger(__name__)

def ffmetafile_read(filepath,mediafilepath=None,return_as="config"):
    if mediafilepath is not None:
        if os.path.exists(filepath):
            os.remove(filepath)

        shell([ffmpeg_path + 'ffmpeg.exe', '-i', '' + mediafilepath + '', '-f', 'ffmetadata', '' + filepath + '', '-y'],
              timeout=20)
    with open(filepath, 'r') as f:
        config_string = '[FFMETADATA1]\n' + f.read()

    logger.debug("The FFMETADATA original contains:\n" + config_string)
    if return_as=="str":
        return config_string
    Config = configparser.ConfigParser(defaults=None, dict_type=multidict, strict=False, allow_no_value=True)
    Config.optionxform = str
    Config.read_string(config_string)
    return Config

def streams_read(filepath,select_streams="v",return_as="config"):
    # detect the time_base of the stream
    result = shell([ffmpeg_path + 'ffprobe.exe', '-show_streams', '-select_streams', select_streams, '' + filepath + ''])
    if return_as=="str":
        return result
    Streams = configparser.ConfigParser(defaults=None, dict_type=multidict, strict=False, allow_no_value=True)
    logger.debug("Found this streams:\n" + result)
    Streams.read_string(result)
    return Streams

def ffmetafile_write(filepath,Config):
    with open(filepath, 'w') as configfile:  # save
        Config.write(configfile, space_around_delimiters=False)
    text_as_string = open(filepath).read().replace('[FFMETADATA1:]', ';FFMETADATA1').replace('[FFMETADATA1]', ';FFMETADATA1')

    regex = r"\[([^:]*)(\:+)\]"
    text_as_string = re.sub(regex, '[\\1]', text_as_string)
    logger.debug("Final ffmetadata\n" + text_as_string)
    with open(filepath, 'w') as configfile:  # save
        configfile.write(text_as_string)
    return text_as_string

def file_path(path):
    if os.path.exists(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_file:{path} is not a valid path")

def timebase_compute(time_base):
    s=time_base.split('/')
    return int(s[0])/int(s[1])

def l(*args):
	return (" ".join(str(a) for a in args))

def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")

def file_is_offline(filepath,return_readable=False):
    fattrs = win32api.GetFileAttributes(filepath)

    ## Define constants for Windows file attributes
    fa = dict(FILE_ATTRIBUTE_READONLY=0x01,
              FILE_ATTRIBUTE_HIDDEN=0x02,
              FILE_ATTRIBUTE_SYSTEM=0x04,
              FILE_ATTRIBUTE_DIRECTORY=0x10,
              FILE_ATTRIBUTE_ARCHIVE=0x20,
              FILE_ATTRIBUTE_NORMAL=0x80,
              FILE_ATTRIBUTE_TEMPORARY=0x0100,
              FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS=0x400000,
              FILE_ATTRIBUTE_NO_SCRUB_DATA=0x20000,
              FILE_ATTRIBUTE_OFFLINE=0x1000,
              FILE_ATTRIBUTE_VIRTUAL=0x10000,
              FILE_ATTRIBUTE_ENCRYPTED=0x4000,
              FILE_ATTRIBUTE_INTEGRITY_STREAM=0x8000,
              FILE_ATTRIBUTE_REPARSE_POINT=0x400,
              FILE_ATTRIBUTE_RECALL_ON_OPEN=0x40000)
    # https://docs.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants
    if return_readable:

        f=[]
        for t, k in fa.items():
            if fattrs & k:
                f.append(t)
        return ','.join(f)
    #print(fattrs,fattrs & fa['FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS'],bool(fattrs & fa['FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS']))

    return (not bool(fattrs & fa['FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS']))


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def fingerprint(imagePath):

    shell([ffmpeg_path+"ffmpeg.exe","-i",imagePath,"-vcodec","png","-ss","20","-vframes","1","-an","-f","rawvideo","-y",os.path.join(TEMP_DIR,"test.png")])

    # load the image and compute the difference hash
    image = Image.open(os.path.join(TEMP_DIR,"test.png"))

    h = str(imagehash.dhash(image))
    image.close()
    os.remove(os.path.join(TEMP_DIR,"test.png"))
    return h

def format_df_rem_col(df2,cols, *args, **kwargs):
    df=df2.copy()
    for c in cols:
        if c in df.columns:
            del df[c]
    return format_df(df,*args,**kwargs)

def format_df( df, *args, **kwargs):
    if 'start_s' in df.columns:
        df.sort_values(by='start_s', inplace=True)
    return '\n' + df.to_string().replace('\n', '\n\t')

def shell(command,verbose=False,timeout=1200):
    try:
        output,cmd_err = subprocess.Popen(command, stderr=subprocess.PIPE,stdout=subprocess.PIPE, universal_newlines=True).communicate()
        #logger.debug("the commandline is {}".format(output.args))
        #output.wait(timeout)
        #output, cmd_err = output
        output=output
        if verbose:
            print(output)
            print(cmd_err)
        else:
            pass
            #logger.info(output)
            #logger.error(cmd_err)
    except subprocess.CalledProcessError as e:
        output = str(e.output)
        #logger.debug("the commandline is {}".format(output.args))

        logger.error(e.stderr)
    #logger.debug(output)
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
    _uniques={}
    def __setitem__(self, key, val):
        if key.startswith('CHAPTER') and (isinstance(val, dict) or  isinstance(val, configparser.SectionProxy)):
            if not type(val).__name__ in self._uniques:
                self._uniques[type(val).__name__] = 1
            else:
                self._uniques[type(val).__name__] += 1
            key += ':' * self._uniques[type(val).__name__]
            #print(key,val)
            #print(self._uniques)
            #print(self.keys())
        #print(key,type(val))
        super().__setitem__(key, val)

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
        logger.debug('\t' * tabs + subkeyname[0] + ' ' + subkeyname[1])
        subkeypath = "%s\\%s" % (keypath, subkeyname)
    return ks

def is_number(n):
    if n==float('nan') or str(n)=='nan':
        return False
    try:
        float(n)   # Type-casting the string to `float`.
                   # If string is not a valid `float`,
                   # it'll raise `ValueError` exception
    except ValueError:
        return False
    print(n)
    return True

