from __future__ import print_function

import datetime
import itertools

from shutil import copyfile

import os
try:
    import winreg as _winreg
except ImportError:  # Python 2
    import _winreg

import configparser

import pandas as pd
import re
from settings import *
from utils import *
from numpy import isclose
from util_copy_with_progressbar import CPprogress

#this is the integration for mpc-be
class chapter_of_mpcbe:

    def load_filelist(self,files):
        # HKEY_CURRENT_USER\Software\MPC-BE\Favorites2\Files
        ks = winreg_traverse_registry_tree(_winreg.HKEY_CURRENT_USER, r"Software\\MPC-BE\\Favorites2\\Files")
        for fav in ks:
            data=fav[1].split('|')

            entry = {'indexed':time_index,'end':None,'src_format':'registry','src_file':'mpc-be','src_id': fav[0],'title':data[0],'dest_file':data[3],'start':data[1]}
            #i = files.index[files['src_id'] == fav[0]].tolist()
            i=files.index[((files['dest_file'] == data[3]) & (files['start']==int(data[1])))].tolist()

            if len(i)>0:
                #here we can think about to remove the chapter from the file
                # because now we will overwrite

                for k,v in entry.items():
                    files.at[i[0],k]=v
                #files.update(pd.Series(entry,name=i),overwrite=True)
            else:
                files=files.append(entry,ignore_index=True)
        lg.debug(format_df(files))
        return files
    def save_filelist(self):
        pass
    def save_file(self,filepath,entries,skip_apply=False):
        lg.debug("Write to file "+filepath+" entry "+format_df(entries))

        chapterfile = r'FFMETADATAFILE' #os.path.basename(filepath)+'-'+str(entry['start'])+
        secure_suffix = ''

        #detect the time_base of the stream
        result = shell([ffmpeg_path+'ffprobe.exe', '-show_streams','' + filepath + ''])

        Streams = configparser.ConfigParser(defaults=None, dict_type=multidict, strict=False, allow_no_value=True)
        lg.debug("Found this streams:\n"+result)
        Streams.read_string(result)
        time_base=1000
        duration=0
        for section in Streams.sections() :
            #finding the longest duration
            if Streams.has_option(section,'duration_ts') and Streams.get(section, 'duration_ts').isnumeric() and duration < int(Streams.get(section, 'duration_ts')):
                #lg.debug('time base=='+Streams.get(section,'time_base'))
                lg.debug('duration==' + Streams.get(section, 'duration_ts'))
                time_base=Streams.get(section,'time_base').split('/')[1]
                if time_base.isnumeric():
                    time_base=int(time_base)
                    lg.debug('time base==' + Streams.get(section, 'time_base'))
                duration = int(Streams.get(section, 'duration_ts'))

        if duration<1:
            lg.error('FOUND NO DURATION FOR FILE BY METADATA. ')
            result = shell([ffmpeg_path + 'ffmpeg.exe', '-i', '"' + filepath + '"',"-f","null","-"])
            regex = r"time=((\d{2}):(\d{2}):(\d{2})\.(\d{1,3}))"
            #https://trac.ffmpeg.org/wiki/FFprobeTips#Getdurationbydecoding
            match = re.search(regex, result)
            lg.debug(result)
            if match!=None:
                print(match.group(1))
                print(((((60*int(match.group(2)))+int(match.group(3)))*60)+int(match.group(4)))*60)
                print(match.group(5))
            return False,{}

        # read the chapters which are already in the file
        if os.path.exists(chapterfile):
            os.remove(chapterfile)

        shell([ffmpeg_path+'ffmpeg.exe','-i','' + filepath + '','-f','ffmetadata','' + chapterfile + '','-y'],timeout=20)
        with open(chapterfile, 'r') as f:
            config_string = '[FFMETADATA1]\n' + f.read()

        lg.debug("The FFMETADATA original contains:\n"+config_string)
        Config = configparser.ConfigParser(defaults=None, dict_type=multidict, strict=False, allow_no_value=True)
        Config.optionxform = str
        Config.read_string(config_string)

        chapters=pd.DataFrame(columns=['section','timebase','start','end','title'])
        for section in Config.sections():
            if section.startswith('CHAPTER'):
                chapters=chapters.append({**{'section':section},**{x.lower():Config.get(section, x) for x in ['TIMEBASE','START','END','title']}},ignore_index=True)
                #remove the section later

                #update the timebase, so that the timebase is consistent over the whole file
                if Config.get(section, "TIMEBASE"):
                    time_base = int(Config.get(section, "TIMEBASE").split('/')[1])
                    lg.debug("Found timebase in existing chapter.. we use now: "+Config.get(section, "TIMEBASE"))

        if chapters.shape[0]==0:
            # add the first chapter
            chapters = chapters.append({'section': '', 'timebase':'1/'+str(time_base),'start':0,'end': 1, 'title':''},ignore_index=True)
        #calculate the start as seconds..
        chapters['start'] = pd.to_numeric(chapters['start'])
        chapters['end'] = pd.to_numeric(chapters['end'])
        chapters['start_s'] =chapters['timebase'].str[2:]
        chapters['start_s']=pd.to_numeric(chapters['start'].astype(int)/chapters['start_s'].astype(int))

        #chapters['start_s'] = pd.to_numeric(chapters['start_s'])
        lg.debug("Before merging with favs the dataframe of the original file looks like:"+format_df(chapters))
        #check whether for the time a entry already exists in the file -> update
        status={}
        for n,entry in entries.iterrows():
            if str(entry['indexed']) != str(time_index):
                lg.info('The chapter "' + entry['title'] + '" was removed in favs for ' + entry[
                    'dest_file'] + '. The chapter will be deleted in a future release.')
                status[n] = "REMOVED"
                chapters=chapters.drop(n)
                continue

            #tolerance is 1sek before and after to avoid duplicates
            if len(chapters[isclose(chapters['start_s'], entry['start']/10000000, rtol=1e-16, atol=1)])>0:
                #we should check also whether the title changed.. else we do not need to update the file
                lg.info("Chapter "+chapters[isclose(chapters['start_s'], entry['start']/10000000, rtol=1e-16, atol=1)]['title']+' is the same like the new one: '+entry['title'])
                chapters.loc[chapters.index[isclose(chapters['start_s'], entry['start']/10000000, rtol=1e-16, atol=1)],'title']=entry['title']
                status[n]="UPDATED"
            else:
                # or else insert
                #10000000*
                lg.info("Checked for duplicates at pos "+str(round(entry['start']/10000000,2))+' for entry '+entry['title'])
                chapters = chapters.append({'section': '', 'timebase':'1/'+str(time_base),'start':str(int(entry['start']/10000000*time_base)),'start_s':entry['start']/10000000,'end': None, 'title':entry['title']},ignore_index=True)
                status[n] = "APPLIED"

        #when we have no status we have also nothing to apply:
        if status=={}:
            lg.info("There is nothing to apply to file. We will not bother the file and return")
            return None,status
        # clean some chapter titles
        chapters['title']=chapters['title'].apply(lambda x: x if (x not in TITLES_NOT_TIDY+[os.path.basename(filepath)]) else "")

        #now we sort by start ascending
        chapters.sort_values(by=['start'],key=lambda col: pd.to_numeric(col),inplace=True)
        #mapping start and end correctly
        chapters['end'] = chapters.start.shift(-1)
        chapters.iloc[-1,chapters.columns.get_loc('end')] = str(duration)
        #chapters=chapters.reset_index(drop=True)

        lg.debug(format_df(chapters))
        lg.debug(str(status))
        #now we change the chapters
        n=2
        for i,values in chapters.iterrows():
            chname=str('CHAPTER'+(':'*n))

            if not Config.has_section(chname):
                Config.add_section('CHAPTER')
                lg.debug(Config.sections())
                Config.set(chname,'TIMEBASE','1/'+str(time_base))
            #now set the other values
            for k in ['START','END','title']:
                Config.set(chname, k,str(values[k.lower()]))
            n+=1

        #kill other sections which might follow afterwards
        lg.debug(Config.sections())
        for i2 in range(n+1,len(Config.sections())+1):
            if Config.has_section(str('CHAPTER'+(':'*int(i2+2)))):
                lg.debug("Removed one section at the of config "+str(i2))
                Config.remove_section(str('CHAPTER'+(':'*int(i2+2))))
            else:
                break

        with open(chapterfile + secure_suffix, 'w') as configfile:  # save
            Config.write(configfile, space_around_delimiters=False)
        text_as_string = open(chapterfile + secure_suffix).read().replace('[FFMETADATA1:]', ';FFMETADATA1')

        regex = r"\[([^:]*)(\:+)\]"
        text_as_string = re.sub(regex, '[\\1]', text_as_string)
        lg.debug("Final ffmetadata\n"+text_as_string)
        with open(chapterfile + secure_suffix, 'w') as configfile:  # save
            configfile.write(text_as_string)

        if not skip_apply:
            #copy temp to read from
            if CAREFUL:
                if not yes_or_no('Do you want to apply the following chapters to '+filepath+':'+format_df(chapters)+'\n'):
                    return (False,status)
            starttime=datetime.datetime.now()
            CPprogress(filepath, as_temp_path(filepath))
            starttime = datetime.datetime.now()-starttime

            print('Expected finishing copying at: '+str(datetime.datetime.now()+starttime))
            shell([ffmpeg_path+'ffmpeg.exe','-i','' +as_temp_path(filepath)+ '','-i','' + chapterfile + secure_suffix + '','-map_metadata','1','-map_chapters','1','-codec','copy','' +
                filepath + '','-y'])
            if os.path.exists(filepath):
                os.remove(as_temp_path(filepath))
                os.remove(chapterfile + secure_suffix)
            else:
                lg.error('Something wrong. Please check the files around-'+filepath+'. Be careful the tempfile is the original file.')
                return (False,status)
            lg.info('Applied metadata to file '+filepath)
            return (True,status)
        return (None,status)
