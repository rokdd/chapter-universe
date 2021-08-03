from __future__ import print_function
import itertools
#import pandas
import configparser
import re
import pandas as pd
from collections import OrderedDict

from mpcbe import *
from settings import *
from utils import *

class chapter_handler:

    chapters_of_mpcbe=chapter_of_mpcbe()
    handler_load_filelist=[chapters_of_mpcbe]
    handler_save_filelist = [chapters_of_mpcbe]
    handler_save_file = [chapters_of_mpcbe]

    files=pd.DataFrame()
    cols = ['indexed','runned', 'applied', 'status', 'src_file', 'src_format', 'src_id', 'title', 'start', 'end', 'dest_file']

    def load_filelist(self,update=False):
        lg.debug('Load filelist')
        # open the filelist from a excel sheet
        self.files = pd.DataFrame()
        if os.path.exists('data.xlsx'):
            self.files = pd.read_excel('data.xlsx', index_col=0)

        self.files = self.files.reindex(self.files.columns.union(self.cols, sort=False), axis=1, fill_value=0)
        self.files['indexed']=self.files['indexed'].astype(str)
        self.files['runned'] = self.files['runned'].astype(str)
        self.files['applied'] = self.files['applied'].astype(str)
        for handler in self.handler_load_filelist:
            self.files=handler.load_filelist(self.files)

        lg.debug('Filelist after loading:'+format_df(self.files))


    def apply_filelist(self):

        for filepath, entries in self.files.sort_values('runned').groupby('dest_file',sort=False):
            lg.debug("Apply "+filepath+" with following chapters "+format_df(entries))

            # check whether the file exists else skip
            if not os.path.exists(filepath):
                lg.error('The following path is not readable: '+filepath)
                continue
            for handler in self.handler_save_file:
                bool_status,status=handler.save_file(filepath,entries,skip_apply=False)
                #means that it was runned without skipping
                if bool_status==True:
                    lg.debug("Good our operation was applied and not skipped or simulated!")
                    self.files.at[entries.index,"runned"] = time_index
                    for i,st in status.items():
                        lg.debug("The operations returned: "+str(i)+' - '+str(st))
                        if st in ['APPLIED','UPDATED','REMOVED']:
                            self.files.at[i,"applied"] = time_index

            self.save()
            if CAREFUL:
                if not yes_or_no('continue to next file'):
                    break


    def close(self):
        # save the files
        self.save()

    def save(self):
        # save the files
        self.files.to_excel('data.xlsx')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    lg.debug('Chapter ridge starts..')
    chapters=chapter_handler()
    chapters.load_filelist(update=True)
    chapters.close()
    chapters.apply_filelist()
    chapters.close()
    lg.debug('Chapter ridge finished!')
    print('Finito')
