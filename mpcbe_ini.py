from __future__ import print_function

import datetime
import itertools

from shutil import copyfile
import os
try:
	import winreg as _winreg
except ImportError:  # Python 2
	import _winreg

from settings import *
from utils import *
from numpy import isclose
from BasicIndexer import BaseIndexer
import configparser


# this is the integration for mpc-be
class chapter_of_mpcbe(BaseIndexer):

	def load_filelist(self, files,directory=None, updatef=False):
		if updatef is False:
			return files
		# HKEY_CURRENT_USER\Software\MPC-BE\Favorites2\Files
		with open(r"C:\Users\rokdd\AppData\Roaming\MPC-BE\favorites.mpc_lst", 'r',encoding='utf-8') as f:
			config_string = f.read()[1:]
		#print(config_string)
		Config = configparser.ConfigParser(defaults=None,  strict=False, allow_no_value=True)
		Config.read_string(config_string)

		ks = Config.sections()
		#print(ks)
		#os.abort()
		#we reset all settings
		files= files.drop(files[(files['src_file']=='mpc-be')&(files['src_format']=='ini')].index)
		for fav in ks:
			data = dict(Config.items(fav))

			# only import what is part of the directory
			if not directory[0]['path'] in os.path.abspath(data['path']):
				print(data['path'])
				print(directory[0]['path'])
				lg.error(data['path']+' not in '+directory[0]['path'])
				continue

			start_ms=data['position'].split(':')
			start_ms=(((int(start_ms[0])*60)+int(start_ms[1]))*60)+int(start_ms[2])
			entry = {**default_entry,**{'file_indexed': time_index,'chapter_indexed': time_index, 'end': None, 'src_format': 'ini', 'src_file': 'mpc-be',
			         'src_id': fav, 'title': data['title'] if data['path']!=data['title'] else '', 'dest_file': data['path'],'timebase':'1/1000', 'start': start_ms, 'start_s': start_ms}}


			# i = files.index[files['src_id'] == fav[0]].tolist()
			i = files.index[((files['dest_file'] == data['path']) & (files['start_s'] == int(start_ms)))].tolist()

			#if len(i) > 0:
				# here we can think about to remove the chapter from the file
				# because now we will overwrite

				#for k, v in entry.items():
				#files.at[i[0], k] = v

				# files.update(pd.Series(entry,name=i),overwrite=True)
				# now we set the file_indexed to all entries (Also for those which was not imported)
				#files.loc[files['dest_file'] == data['path'],"file_indexed"]=time_index
			#else:
			files = files.append(entry, ignore_index=True)

		lg.debug(format_df(files))
		#os.abort()
		return files

	def save_filelist(self):
		pass

	def save_file(self, filepath, entries, skip_apply=False):
		return super().save_file(filepath,entries,skip_apply=skip_apply)
