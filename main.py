from __future__ import print_function
import itertools
import configparser
import os
import re

import numpy
import pandas as pd
from collections import OrderedDict

# that is the old version to read the windows registry
#from mpcbe_winreg import *
from mpcbe_ini import *
from settings import *
from utils import *
import sys
from BasicIndexer import chapter_of_basic_files,BaseIndexer
from util_copy_with_progressbar import CPprogress


class chapter_handler:

    chapters_of_mpcbe=chapter_of_mpcbe()
    chapters_of_basic = chapter_of_basic_files()
    handler_load_filelist=[chapters_of_mpcbe,chapters_of_basic]
    handler_tidy_filelist = [chapters_of_basic]
    handler_save_filelist = [chapters_of_basic]
    handler_save_file = [chapters_of_basic]


    files=pd.DataFrame()
    cols = default_columns

    def load_filelist(self,updatef=False):
        lg.debug('Load filelist '+PATH_DATA_FILE)
        # open the filelist from a excel sheet
        self.files = pd.DataFrame()

        if os.path.exists(PATH_DATA_FILE):
            self.files = pd.read_excel(PATH_DATA_FILE, index_col=0)

        self.files = self.files.reindex(self.files.columns.union(self.cols, sort=False), axis=1, fill_value=0)
        self.files['file_indexed']=pd.to_datetime(self.files['file_indexed'].replace('0',numpy.NaN))
        self.files['chapter_indexed']=pd.to_datetime(self.files['chapter_indexed'].replace('0',numpy.NaN))
        self.files['runned'] = pd.to_datetime(self.files['runned'].replace('0',numpy.NaN))
        self.files['applied'] = pd.to_datetime(self.files['applied'].replace('0',numpy.NaN))
        self.files = self.files.astype({"title": str})

        #now lets index all registered handlers
        for handler in self.handler_load_filelist:
            self.files=handler.load_filelist(self.files,updatef=updatef,directory=MAIN_DIRS)

        #generate the fingerprints for all added filesy
        for filepath, entries in self.files.groupby('dest_file',sort=False):
            if entries[entries['fingerprint'].isin(["","NaN"])].shape[0]==0:
                lg.debug('File is fingerprinted: %s' % filepath)
                continue
            #print(entries[entries['fingerprint'] == ""].shape[0])

            if os.path.exists(filepath):
                if not file_is_offline(filepath):
                    lg.debug('File not offline: %s' % (filepath))
                    continue
                self.files.loc[entries.index,"fingerprint"] = fingerprint(filepath)
            else:
                lg.debug('File not readable: %s' % (filepath))

        lg.debug('Filelist after loading:'+format_df(self.files))


    def tidy_filelist(self):
        bool_status=None
        for finger_path, entries in self.files.sort_values('runned').groupby('fingerprint',sort=False):
            entries.sort_values(by='start_s',inplace=True)
            for filepath,entries2 in self.files[self.files['fingerprint']==finger_path].sort_values('runned').groupby('dest_file',sort=False):
                if os.path.exists(filepath) and not file_is_offline(filepath):
                    lg.error('The following path is not offline: '+filepath)
                    bool_status = False
                    continue
                #if bool_status!=None and CAREFUL:
                #    if not yes_or_no('continue with file '+filepath+" with following chapters "+format_df(entries)):
                #        break

                # check whether the file exists else skip
                if not os.path.exists(filepath):
                    lg.error('The following path is not readable: '+filepath)
                    bool_status = False
                    continue
                if not file_is_offline(filepath):
                    lg.error('The following path is not offline: '+filepath+' '+file_is_offline(filepath,return_readable=True))
                    bool_status = False
                    continue
                for handler in self.handler_tidy_filelist:
                    bool_status,status,self.files=handler.tidy_file(filepath,entries2,self.files,finger_path,skip_apply=False)


    def apply_filelist(self):
        bool_status=None
        for finger_path, entries in self.files.sort_values('runned').groupby('dest_file',sort=False):
            entries.sort_values(by='start_s',inplace=True)
            for filepath,entries2 in self.files[self.files['dest_file']==finger_path].sort_values('runned').groupby('dest_file',sort=False):
                if os.path.exists(filepath) and not file_is_offline(filepath):
                    lg.error('The following path is not offline: '+filepath)
                    bool_status = False
                    continue
                #if bool_status!=None and CAREFUL:
                #    if not yes_or_no('continue with file '+filepath+" with following chapters "+format_df(entries)):
                #        break
                lg.debug("Apply "+str(filepath)+" [dest_file="+str(finger_path)+"] with following chapters "+str(format_df(entries))+"\n entries2"+str(format_df(entries2)))

                # check whether the file exists else skip
                if not os.path.exists(filepath):
                    lg.error('The following path is not readable: '+filepath)
                    bool_status = False
                    continue
                if not file_is_offline(filepath):
                    lg.error('The following path is not offline: '+filepath+' '+file_is_offline(filepath,return_readable=True))
                    bool_status = False
                    continue
                for handler in self.handler_save_file:
                    bool_status,status=handler.save_file(filepath,entries,skip_apply=False)
                    #means that it was runned without skipping
                    if bool_status==True:
                        lg.debug("Good our operation was applied and not skipped or simulated!")
                        self.files.loc[entries2.index,"runned"] = time_index
                        for i,st in status.items():
                            lg.debug("The operations returned: "+str(i)+' - '+str(st))
                            if st in ['APPLIED','UPDATED','REMOVED']:
                                self.files.loc[i,"applied"] = time_index


        self.save()

    def close(self):
        # save the files
        self.save()

    def save(self):
        # save the files

        with pd.ExcelWriter(PATH_DATA_FILE,mode="w",engine="openpyxl") as writer:
            self.files.to_excel(writer)

import argparse
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--index-only', help='index only files',default=False,type=str2bool)
    parser.add_argument('--index', help='index files',default=True,type=str2bool)
    parser.add_argument('--tidy', help='tidy chapters of files', default=True,type=str2bool)
    parser.add_argument('--apply', help='apply chapters to files', default=True,type=str2bool)
    parser.add_argument('--careful', help='ask before write files', default=True, type=str2bool)
    parser.add_argument('--directory', help='scan directory for files', type=dir_path)

    parser.add_argument('--data-file', help='keep data',default="data.xlsx", type=file_path)
    parser.add_argument('--strip-chapters', help='strip chapter of filepath',default=None, type=file_path)

    parser.add_argument('--fix-duration', help='fix duration',default=None, type=file_path)
    parser.add_argument('--dump-file', help='show informations about the file', default=None, type=file_path)

    args = parser.parse_args()

    if hasattr(args,"dump_file"):
        if getattr(args, "dump_file") is not None:
            print('dump_file of %s' % (getattr(args, "dump_file")))
            print('===CHAPTERS===')
            print(ffmetafile_read(chapterfile + secure_suffix, getattr(args, "dump_file"),return_as='str'))
            print('===STREAMS===')
            print(
                streams_read(getattr(args, "dump_file"), return_as='str'))


            os.abort()
    if hasattr(args,"strip_chapters"):
        if getattr(args,"strip_chapters") is not None:
            print('Strip chapters of %s'%(getattr(args,"strip_chapters")))
            CPprogress(getattr(args,"strip_chapters"), as_temp_path(getattr(args,"strip_chapters")))
            #generate a empty ffmetadatafile
            Config=ffmetafile_read(chapterfile + secure_suffix, as_temp_path(getattr(args,"strip_chapters")))
            lg.debug(Config.sections())

            for i2 in range(0, len(Config._proxies) + 1):
                if Config.has_section(str('CHAPTER' + (':' * int(i2 + 1)))):
                    lg.debug("Removed one section at the of config " + str(i2))
                    Config.remove_section(str('CHAPTER' + (':' * int(i2 + 1))))
                else:
                    break

            ffmetafile_write(chapterfile + secure_suffix, Config)

            shell([ffmpeg_path + 'ffmpeg.exe', '-i', '' + as_temp_path(getattr(args,"strip_chapters")), '-i',
			       '' + chapterfile + secure_suffix + '','-map_metadata','1', '-map_metadata', '1', '-map_chapters', '1', '-codec', 'copy',
                   '' + getattr(args,"strip_chapters") + '', '-y'])
            # todo remove temp file in future
            os.abort()

        if hasattr(args, "fix_duration"):
            if getattr(args, "fix_duration") is not None:
                print('fix_duration of %s' % (getattr(args, "fix_duration")))
                CPprogress(getattr(args, "fix_duration"), as_temp_path(getattr(args, "fix_duration")))
                # get the config file which exists
                Config = ffmetafile_read(chapterfile + secure_suffix, as_temp_path(getattr(args, "fix_duration")))

                lg.debug(Config.sections())
                # and get the streams
                dummyIndexer=BaseIndexer()
                time_base,duration,duration_s,Streams=dummyIndexer.get_time_infos(as_temp_path(getattr(args, "fix_duration")))
                lg.debug(time_base)
                lg.debug(duration)
                chapters,config=dummyIndexer.file_get_chapters(as_temp_path(getattr(args, "fix_duration")))
                lg.debug(chapters)
                if chapters.at[0,'end']==0:
                    lg.debug("Looks like file has no chapters ")
                    os.abort()

                print('LAST CHAPTER IS:')
                print(chapters.iloc[-1])

                duration_stream = duration / time_base
                print('Calculated duration based of streams: ','%d / %d = %d'%(duration,time_base,duration_stream))

                duration_chapter=chapters.iloc[-1]['end']*timebase_compute(chapters.iloc[-1]['timebase'])
                print('Calculated duration based of last chapter: ',duration_chapter)

                diff=duration_stream-duration_chapter

                print('The difference: ',diff)
                if abs(diff)<2:
                    print('The difference is very low, no action required')
                    os.abort()

                #calculate new duration
                target_duration=duration_stream/timebase_compute(chapters.iloc[-1]['timebase'])

                # should we change all chapters to convert or only the last one?
                faktor_convert=duration_stream/duration_chapter
                print(duration_stream/duration_chapter,(time_base/1*timebase_compute(chapters.iloc[-1]['timebase'])))


                if yes_or_no('Do you want to apply the factor '+str(faktor_convert)+' to ' + getattr(args,
                                                                                         "fix_duration") + ':' + format_df(
                        chapters) + "\n"):
                    for section in Config.sections():
                        if section.startswith('CHAPTER'):
                            Config.set(section, 'END', str(faktor_convert*Config.get(section,'END')))
                            Config.set(section, 'START', str(faktor_convert * Config.get(section, 'START')))

                else:
                    print("New duration which will be written to last chapter:", target_duration)
                    chapters.at[:-1, 'end'] = target_duration
                    Config.set(Config.sections()[-1], 'END', str(target_duration))


                if yes_or_no('Do you want to apply the following chapters to ' + getattr(args, "fix_duration") + ':' + format_df(
                        chapters) + "\n"):

                    ffmetafile_write(chapterfile + secure_suffix, Config)
                    pass

                    shell([ffmpeg_path + 'ffmpeg.exe', '-i', '' + as_temp_path(getattr(args, "fix_duration")) + '', '-i',
                           '' + chapterfile + secure_suffix + '', '-map_metadata', '1', '-map_chapters', '1', '-codec',
                           'copy', '' + getattr(args, "fix_duration") + '', '-y'])
                    print("Changed original file "+getattr(args, "fix_duration")+'. The temp file can be removed when(!!!) you are satiesfied. Running again will remove tempfile!')
                else:
                    print('Abort')
                # todo remove temp file in future
                os.abort()

    if hasattr(args,"directory") and getattr(args,"directory") is not None:
        lg.info("Changed the main directories by argument to:"+args.directory)
        MAIN_DIRS=[{'path':args.directory}]

    if hasattr(args,"data_file") and getattr(args,"data_file") is not None:
        lg.info("Changed data file path to :"+args.data_file)
        PATH_DATA_FILE=args.data_file

    lg.debug('Chapter ridge starts..')
    chapters=chapter_handler()

    CAREFUL=args.careful

    lg.debug(l('='*5,'INDEX','='*5))
    chapters.load_filelist(updatef=args.index)

    chapters.close()
    if args.index_only:
        lg.info("Indexed, finished")
        os.abort()
    if args.tidy:
        lg.debug(l('=' * 5, 'TIDY', '=' * 5))
        chapters.tidy_filelist()
        chapters.close()
    if args.apply:
        lg.debug(l('=' * 5, 'APPLY', '=' * 5))
        chapters.apply_filelist()
        chapters.close()
    lg.debug('Chapter ridge finished!')
    print('Finito')
