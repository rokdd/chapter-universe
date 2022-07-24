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

# this is the integration for mpc-be
class chapter_of_mpcbe(BaseIndexer):

	def load_filelist(self, files, updatef=False):
		if updatef is False:
			return files
		# HKEY_CURRENT_USER\Software\MPC-BE\Favorites2\Files
		ks = winreg_traverse_registry_tree(_winreg.HKEY_CURRENT_USER, r"Software\\MPC-BE\\Favorites2\\Files")
		for fav in ks:
			data = fav[1].split('|')

			entry = {**default_entry,**{'file_indexed': time_index,'chapter_indexed': time_index, 'end': None, 'src_format': 'registry', 'src_file': 'mpc-be',
			         'src_id': fav[0], 'title': data[0], 'dest_file': data[3], 'start': data[1]}}
			# i = files.index[files['src_id'] == fav[0]].tolist()
			i = files.index[((files['dest_file'] == data[3]) & (files['start'] == int(data[1])))].tolist()

			if len(i) > 0:
				# here we can think about to remove the chapter from the file
				# because now we will overwrite

				for k, v in entry.items():
					files.at[i[0], k] = v
				# files.update(pd.Series(entry,name=i),overwrite=True)
				# now we set the file_indexed to all entries (Also for those which was not imported)
				files.loc[files['dest_file'] == data[3],"file_indexed"]=time_index
			else:
				files = files.append(entry, ignore_index=True)

		lg.debug(format_df(files))
		return files

	def save_filelist(self):
		pass

	def save_file(self, filepath, entries, skip_apply=False):
		return super().save_file(filepath,entries,skip_apply=skip_apply)
