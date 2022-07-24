import os
import sys
import tempfile




def find_FFMEG(**args):
    localFFMPEG = None
    locations = ['/opt/local/bin', '/usr/local/bin', '/usr/local/ffmpeg', '/usr/local/opt/']
    for location in locations:
        if os.path.isfile("/".join([location, 'ffmpeg'])):
            localFFMPEG = "/".join([location, 'ffmpeg'])
    return localFFMPEG


# THESE ARE DEFAULT SETTINGS..
ffmpeg_path = os.getenv('FFMPEG',  find_FFMEG())
ffmpeg_path=r'C:\Users\rokdd\Documents\Eigene-Programme\50_Portables\ffmpeg\bin'+chr(92)

DEBUG=True
VERBOSE=True
#not used currently
BACKUP=True

#asks after and before each chapter to continue or not
CAREFUL=True

MAIN_DIRS=[{'path':'.'}]

MAIN_SUFFIX=[".mkv",".mp4",".m4v",".mpg",".mpeg",".wmv",".vdr"]

MAIN_FILES_IGNORE=["index.vdr",'info.vdr']

PATH_DATA_FILE="data.xlsx"

TEMP_DIR=tempfile.gettempdir()

# HERE IT IS MORE CONFIG DO NOT CHANGE THIS-->>>>>>>>>

#list of titles which will be set empty if they match (the filename as a chapter name gets always replaced!)
chapterfile = r'FFMETADATAFILE'  # os.path.basename(filepath)+'-'+str(entry['start'])+
secure_suffix = ''

TITLES_NOT_TIDY=["Start","Ende","End"]

import datetime as dt
time_index=dt.datetime.now()

import logging
logging.basicConfig(filename='chapter-universe.log',filemode='a',format='%(asctime)s %(name)s %(funcName)s %(levelname)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG if DEBUG else logging.info)
lg=logging.getLogger('main')
if VERBOSE:
    lg.addHandler(logging.StreamHandler())

default_entry={'file_indexed': time_index,"chapter_indexed":time_index, 'end': None, 'src_format': 'registry', 'src_file': 'mpc-be',
			         'src_id': "", 'title': "", 'dest_file': "", 'start': None, 'fingerprint': ''}

default_columns=['file_indexed','chapter_indexed','runned', 'applied', 'status', 'src_file', 'src_format', 'src_id', 'title', 'start', 'end', 'dest_file','fingerprint']