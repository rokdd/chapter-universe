from __future__ import print_function
import configparser
from utils import *
import pandas as pd
import re
import os
from settings import *
import pathlib
import win32con

import datetime
import itertools
from shutil import copyfile
from numpy import isclose
from util_copy_with_progressbar import CPprogress

import win32api

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

COLUMNS_FILES=['dest_file','src_id','src_file','src_format','fingerprint']

class BaseIndexer:

	def file_get_config(self, filepath):
		chapterfile = r'FFMETADATAFILE'  # os.path.basename(filepath)+'-'+str(entry['start'])+
		return ffmetafile_read(chapterfile,filepath)

	def file_get_chapters(self, filepath, time_base=1000, Config=None):
		# read the chapters which are already in the file
		if Config is None:
			Config = self.file_get_config(filepath)

		chapters = pd.DataFrame(columns=['section', 'timebase', 'start', 'end', 'title'])
		for section in Config.sections():
			if section.startswith('CHAPTER'):
				chapters = chapters.append({**{'section': section}, **{x.lower(): Config.get(section, x) for x in
				                                                       ['TIMEBASE', 'START', 'END', 'title']}},
				                           ignore_index=True)
				# remove the section later

				# update the timebase, so that the timebase is consistent over the whole file
				#if Config.get(section, "TIMEBASE"):
				#	#time_base = int(Config.get(section, "TIMEBASE").split('/')[1])
				#	logger.debug("Found timebase in existing chapter.. " + Config.get(section, "TIMEBASE"))

		if chapters.shape[0] == 0:
			# add the first chapter
			chapters = chapters.append(
				{'section': '', 'timebase': '1/' + str(time_base), 'start': 0, 'end': 0, 'title': ''},
				ignore_index=True)
		# calculate the start as seconds..
		chapters['start'] = pd.to_numeric(chapters['start'])
		chapters['end'] = pd.to_numeric(chapters['end'])
		chapters['start_s'] = chapters['timebase'].str[2:]
		chapters['start_s'] = pd.to_numeric(chapters['start'].astype(int) / chapters['start_s'].astype(int))
		chapters.sort_values(by=['start_s'], key=lambda col: pd.to_numeric(col), inplace=True)
		return (chapters, Config)

	def get_time_infos(self,filepath,duration=0,time_base=1000):
		Streams=streams_read(filepath)

		for section in Streams.sections():
			# finding the longest duration
			if Streams.has_option(section, 'duration_ts') and Streams.get(section,
			                                                              'duration_ts').isnumeric() and duration < int(
				Streams.get(section, 'duration_ts')):
				# logger.debug('time base=='+Streams.get(section,'time_base'))
				logger.debug('duration_ts==' + Streams.get(section, 'duration_ts'))
				logger.debug('duration_s==' + Streams.get(section, 'duration'))
				time_base = Streams.get(section, 'time_base').split('/')[1]
				if time_base.isnumeric():
					time_base = int(time_base)
					logger.debug('time base==' + Streams.get(section, 'time_base'))
				duration = int(Streams.get(section, 'duration_ts'))
				duration_s = float(Streams.get(section, 'duration'))

		# maybe later we can use: duration_ts / timebase = duration

		if duration < 1:
			logger.error('FOUND NO DURATION FOR FILE BY METADATA. ')
			result = shell([ffmpeg_path + 'ffmpeg.exe', '-i', '"' + filepath + '"', "-f", "null", "-"])
			regex = r"time=((\d{2}):(\d{2}):(\d{2})\.(\d{1,3}))"
			# https://trac.ffmpeg.org/wiki/FFprobeTips#Getdurationbydecoding
			match = re.search(regex, result)
			logger.debug(l("result:",result))
			print(match)
			if match != None:
				print(match.group(1))
				print(((((60 * int(match.group(2))) + int(match.group(3))) * 60) + int(match.group(4))) * 60)
				print(match.group(5))
			return False, False,False, False
		return time_base,duration,duration_s,Streams

class chapter_of_basic_files(BaseIndexer):
	def load_filelist(self, files, directory=None, updatef=False):
		if updatef is False:
			return files

		logger.debug("Index %s from filesystem" % (directory[0]['path']))
		for path, subdirs, files_list in os.walk(directory[0]['path']):
			for name in files_list:
				logger.debug("Index %s from filesystem" % (os.path.join(path, name)))
				if not pathlib.Path(name).suffix in MAIN_SUFFIX or name in MAIN_FILES_IGNORE or name.startswith('temp-'):
					continue
				if not file_is_offline(os.path.join(path, name)):
					continue

				entry = {**default_entry,
				         **{'file_indexed': time_index, 'chapter_indexed': time_index, 'src_format': 'file',
				            'src_file': 'basic_files',
				            'src_id': os.path.join(path, name), 'title': "", "start": 0,
				            'fingerprint': fingerprint(os.path.join(path, name)),


				            'dest_file': os.path.join(path, name)}}

				# read the time infos

				time_base, duration, duration_s, Streams = super().get_time_infos(os.path.join(path, name))

				if not time_base:
					continue

				# import the chapters
				(chapters, Config) = super().file_get_chapters(os.path.join(path, name),time_base=time_base)
				logger.debug(l("Chapters from file before merge:",chapters))
				#chapters = pd.concat([pd.DataFrame([entry]*len(chapters)), chapters], axis=1)
				for k,v in entry.items():
					if k not in chapters.columns:
						chapters[k]=v
				logger.debug(l("Chapters from file after merge:",chapters))

				#remove all chapters from this file AND this plugin
				files.drop(files[(files['src_file']=="basic_files")&(files['dest_file']==os.path.join(path, name))].index, inplace=True)

				if(len(chapters)>1):
					pass
					#os.abort()
				for kchapter,chapter in chapters.iterrows():
					logger.debug(l("Iterate over Chapters, so we have #%s:"%kchapter,chapter))

					#print(files)
					# i = files.index[files['src_id'] == fav[0]].tolist()
					i = files.index[((files['dest_file'] == os.path.join(path, name)) & (files['start_s'] == int(chapter["start_s"])))].tolist()

					#print(i,chapter["start"])
					#print(files[((files['dest_file'] == os.path.join(path, name)))])
					#print(files[((files['dest_file'] == os.path.join(path, name)) & (
					#			files['start_s'] == int(chapter["start_s"])))])

					if len(i) > 0:
						# here we can think about to remove the chapter from the file
						# because now we will overwrite

						for k, v in chapter.items():
							logger.debug(l(k," == ",v))
							files.at[i[0], k] = v

						# files.update(pd.Series(entry,name=i),overwrite=True)
						# now we set the file_indexed to all entries (Also for those which was not imported)
						files.loc[files['dest_file'] == os.path.join(path, name), "file_indexed"] = time_index
						logger.debug("Updated %s to files with following chapter: \n%s" % (
							os.path.join(path, name), str(chapter)))
					else:
						logger.debug("Appended %s to files with following chapter: \n%s" % (
						os.path.join(path, name), str(chapter)))
						files = files.append(chapter.to_dict(), ignore_index=True)

		files.sort_values(by=['start'], key=lambda col: pd.to_numeric(col), inplace=True)
		# mapping start and end correctly. not the correct time here..might destory more data as we would like to keep
		#files['end'] = files.start.shift(-1)

		logger.debug(format_df(files))
		return files


	def tidy_file(self, filepath, entries,files,finger_path, skip_apply=False):
		logger.debug("Tidy file " + filepath + " entry " + format_df_rem_col(
						entries,COLUMNS_FILES))

		chapterfile = r'FFMETADATAFILE'  # os.path.basename(filepath)+'-'+str(entry['start'])+
		secure_suffix = ''

		(time_base,duration,duration_s,streams)=super().get_time_infos(filepath)

		if duration==False:
			return False,False,files

		# read the chapters which are already in the file
		(chapters, Config) = super().file_get_chapters(filepath, time_base=time_base)

		# chapters['start_s'] = pd.to_numeric(chapters['start_s'])
		logger.debug("Before merging with favs the dataframe of the original file looks like:" + format_df_rem_col(
						chapters,COLUMNS_FILES))

		# check whether for the time a entry already exists in the file -> update

		for n,entry in files[((files['fingerprint']==finger_path) & ((files['src_file']!='basic_files') | (files["dest_file"]!=filepath)))].iterrows():
			#print(entry)

			# when this chapter was indexed not at the time of the last check of the file it is removed. the last check of file is when the file was seen
			#if str(entry['chapter_indexed']) != str(entry['file_indexed']):
			#	logger.info('The chapter #' + str(n) + '/'  + ' "' + str(
			#		entry['title']) + '" was removed in favs for ' + str(entry[
			#			                                                     'dest_file']) + '. The chapter will be deleted in a future release.')

			#status[entry['start']] = "REMOVED"
			#	logger.debug(l('We should drop',n))
			#chapters = chapters.drop(n, axis=0)
			#continue

			# tolerance is 1sek before and after to avoid duplicates rtol=1e-16,
			if len(files[((files["dest_file"]==filepath)&(files['src_file']=='basic_files') & (isclose(files['start_s'], entry['start_s'] ,  atol=1)))]) > 0:
				# we should check also whether the title changed.. else we do not need to update the file
				#print(chapters['start_s'].values,entry['start_s'],entry['start'],entry['start'] / 10000000)


				if files[((files["dest_file"]==filepath)&(files['src_file']=='basic_files') & (isclose(files['start_s'], entry['start_s'] , atol=1)) &
				             (files['title']==entry['title']))].shape[0]>0:

					logger.info(
						"Chapter " + files[((files["dest_file"]==filepath)&(files['src_file']=='basic_files') & (isclose(files['start_s'], entry['start_s'] ,  atol=1)))][
								'title'].values[0] + ' is the same like the new one: #%s %s'%(str(n),str(entry['title'])))
					# we just eat the entry

				else:
					# / 10000000
					logger.info(
						"Chapter " + str(files[((files["dest_file"]==filepath)&(files['src_file']==entry['src_file']) & (isclose(files['start_s'], entry['start_s'], atol=1)))][
							'title'].values[0]) + ' is the same like the new one with new title: ' + str(entry['title']))
					files.loc[files.index[((files["dest_file"]==filepath)&(files['src_file']==entry['src_file'])  & (isclose(files['start_s'], entry['start_s'] , atol=1)))], 'title'] = entry['title']

					#status[entry['start']] = "UPDATED"
			else:

				# or else insert
				# 10000000*
				logger.info(
					"Checked for duplicates at pos " + str(round(entry['start'] / 10000000, 2)) + ' for entry ' + entry[
						'title'])
				files = files.append({**entry,**{'section': '','src_file':"basic_files","dest_file":filepath, 'timebase': '1/' + str(time_base),
				                            'start': str(int(float(entry['start_s']) / 1000 * 1000 *  time_base)) if is_number(entry['start_s']) else "0",
				                            'start_s': entry['start_s'] , 'end': None, 'title': entry['title']}},
				                           ignore_index=True)



				#status[entry['start']] = "APPLIED"
			#print('=======================')

		entries=files[((files["dest_file"]==filepath) & (files['src_file']=="basic_files"))]

		# clean some chapter titles
		entries['title'] = entries['title'].apply(
			lambda x: x if (x not in TITLES_NOT_TIDY + [os.path.basename(filepath),filepath,'nan']) else "")

		#clean the start_s by start and time_base
		entries['start_s'] = entries['timebase'].str[2:]
		entries['start_s'] = pd.to_numeric(entries['start'].astype(float) / entries['start_s'].astype(float))

		# now we sort by start ascending
		entries.sort_values(by=['start_s'], key=lambda col: pd.to_numeric(col), inplace=True)

		# TODO: we should check what is over the duration and remove them..

		# TODO: We should also only use one time base (from the streams)
		entries['start'] = entries['start_s']*time_base
		entries['timebase']='1/%d'%time_base


		# mapping start and end correctly
		entries['end'] = entries.start.shift(-1)
		#logger.debug(l("chapters",format_df(chapters)))
		entries.iloc[-1, entries.columns.get_loc('end')] = str(duration)
		# chapters=chapters.reset_index(drop=True)

		files.update(entries)
		print(files)

		logger.debug(l("chapters after tidy",format_df_rem_col(entries,COLUMNS_FILES)))
		#logger.debug(str(status))

		return (None, {},files)


	def save_file(self, filepath, entries, skip_apply=False):
		logger.debug("Apply to file " + filepath + " entry " + format_df(entries))

		chapterfile = r'FFMETADATAFILE'  # os.path.basename(filepath)+'-'+str(entry['start'])+
		secure_suffix = ''

		(time_base,duration,duration_s,streams)=super().get_time_infos(filepath)

		if duration==False:
			return False,False


		# read the chapters which are already in the file
		(chapters2, Config) = super().file_get_chapters(filepath, time_base=time_base)

		# we save only our own data
		chapters=entries[entries['src_file']=='basic_files']
		if not chapters.shape[0]>1:
			return (False,{})
		#logger.debug(format_df(chapters))
		#logger.debug(str(status))
		status=dict()

		#logger.debug(l(Config.sections(),Config._proxies,Config._proxies._uniques['SectionProxy']))
		for section in Config.sections():
			if section.startswith('CHAPTER'):
				Config.remove_section(section)
		#first we remove all chapters from the config

		n=0
		for i, values in chapters.iterrows():
			chname = str('CHAPTER' + (':' * n))

			if not Config.has_section(chname):
				Config.add_section('CHAPTER')
				chname = str('CHAPTER' + (':' * Config._proxies._uniques['SectionProxy']))
				Config.set(chname, 'TIMEBASE', '1/' + str(time_base))
			# now set the other values
			for k in ['START', 'END', 'title']:
				Config.set(chname, k, str(values[k.lower()]))
			n += 1

		# kill other sections which might follow afterwards
		for i2 in range(n , len(Config.sections()) + 1):
			if Config.has_section(str('CHAPTER' + (':' * int(i2 + 1)))):
				logger.debug("Removed one section at the of config " + str(i2))
				Config.remove_section(str('CHAPTER' + (':' * int(i2 + 1))))
			else:
				break

		ffmetafile_content=ffmetafile_write(chapterfile + secure_suffix,Config)

		if not skip_apply:

			# copy temp to read from
			if CAREFUL:
				print('======%s======'%(chapterfile + secure_suffix))
				print(ffmetafile_content)
				if not yes_or_no('Do you want to apply the following chapters to ' + filepath + ':' + format_df_rem_col(
						chapters,COLUMNS_FILES) + "\n\nand the following status"+str(status)):

					return (False, status)
			starttime = datetime.datetime.now()
			CPprogress(filepath, as_temp_path(filepath))
			starttime = datetime.datetime.now() - starttime

			print('Expected finishing copying at: ' + str(datetime.datetime.now() + starttime))
			shell([ffmpeg_path + 'ffmpeg.exe', '-i', '' + as_temp_path(filepath) + '', '-i',
			       '' + chapterfile + secure_suffix + '', '-map_metadata', '1', '-map_chapters', '1', '-codec', 'copy',
			       '' + filepath + '', '-y'])
			if os.path.exists(filepath):
				os.remove(as_temp_path(filepath))
				os.remove(chapterfile + secure_suffix)
			else:
				logger.error(
					'Something wrong. Please check the files around-' + filepath + '. Be careful the tempfile is the original file.')
				return (False, status)
			logger.info('Applied metadata to file ' + filepath)
			return (True, status)
		return (None, status)

	def save_filelist(self):
		pass
