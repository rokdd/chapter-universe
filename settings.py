ffmpeg_path=r'C:\Users\rokdd\Documents\Eigene-Programme\50_Portables\ffmpeg\bin'+chr(92)
DEBUG=True
#not used currently
BACKUP=True

#asks after and before each chapter to continue or not
CAREFUL=True

import datetime as dt
time_index=dt.datetime.now()

import logging

logging.basicConfig(filename='chapter-universe.log',filemode='a',format='%(asctime)s %(name)s %(funcName)s %(levelname)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S',level=logging.DEBUG if DEBUG else logging.info)

lg=logging.getLogger('main')

#logging.basicConfig(level=logging.DEBUG)