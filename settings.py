import os


def cli(**kwargs):
    parser = argparse.ArgumentParser()
    parser.prog = program
    parser.description = description
    parser.epilog = epilog

    # Defaults for all programs
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' + version)

    parser.add_argument('-d', '--debug',
                        help='Turn on Debugging Mode',
                        action='store_true',
                        required=False,
                        dest='DEBUG',
                        default=True
                        )

    parser.add_argument('-f', '--chapters-file',
                        help='Text file with chapters in it. TimeStamp space Title',
                        type=str,
                        action='store',
                        required=False,
                        dest='CHAPTERS',
                        default=CHAPTERS
                        )

    parser.add_argument('-m', '--mpeg-video',
                        help='Movie file MP4s only -- Currently no checking',
                        type=str,
                        action='store',
                        required=False,
                        dest='FILENAME',
                        default="unknown"
                        )

    parser.add_argument('-o', '--mpeg-video-markers',
                        help='default is FILENAME_chapters.mp4',
                        type=str,
                        action='store',
                        required=False,
                        dest='OUTPUT',
                        default=FILENAME + "_chapters.mp4"
                        )
    parser.add_argument('-t', '--title',
                        help='''default is My Default Movie,
                             this is the title that will show when playing''',
                        type=str,
                        action='store',
                        required=False,
                        dest='TITLE',
                        default="My Default Movie"
                        )

    parser.add_argument('--test',
                        help='''test if ffmpeg is installed and the program runs,''',
                        action='store_true',
                        required=False,
                        dest='testProgram',
                        default=False
                        )

    parse_out = parser.parse_args()
    return parse_out


def setup(configuration):
    global DEBUG
    global ffmpeg_path
    ffmpeg_path = os.getenv('FFMPEG',  find_FFMEG())


def find_FFMEG(**args):
    localFFMPEG = None
    locations = ['/opt/local/bin', '/usr/local/bin', '/usr/local/ffmpeg', '/usr/local/opt/']
    for location in locations:
        if os.path.isfile("/".join([location, 'ffmpeg'])):
            localFFMPEG = "/".join([location, 'ffmpeg'])
    return localFFMPEG


# THESE ARE DEFAULT SETTINGS..
ffmpeg_path=r'C:\Users\rokdd\Documents\Eigene-Programme\50_Portables\ffmpeg\bin'+chr(92)
DEBUG=True
#not used currently
BACKUP=True

#asks after and before each chapter to continue or not
CAREFUL=True

#list of titles which will be set empty if they match (the filename as a chapter name gets always replaced!)
TITLES_NOT_TIDY=["Start","Ende","End"]

import datetime as dt
time_index=dt.datetime.now()

import logging

logging.basicConfig(filename='chapter-universe.log',filemode='a',format='%(asctime)s %(name)s %(funcName)s %(levelname)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG if DEBUG else logging.info)

lg=logging.getLogger('main')
