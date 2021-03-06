#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
CPprogress(SOURCE, DESTINATION)

I made this to give shutil.copy() [or shutil.copy2() in this case] a progress bar.

You can use CPprogress(SOURCE, DESTINATION) just like shutil.copy(src, dst). SOURCE must be a file path and DESTINATION a file or folder path.

It will give you a progress bar for each file copied. Just copy this code above the place where you want to use CPprogress(SOURCE, DESTINATION) in your code.

You can easily change the look of the progress bar:
    - To keep the style and just change the colors, replace the colors values of progressCOLOR and finalCOLOR (orange code at the end of the lines).
    - The use a solid block progress bar, # -*- coding: utf-8 -*- is required. Otherwise, you will get an encoding error. Some basic terminals, like xterm, may not show the progress bar because of the utf-8 characters.
      To use this style, remove the comments #STYLE# in lines ###COLORS### - BlueCOLOR and endBLOCK.
      In def getPERCECENTprogress() remove the comments  #STYLE# AND COMMENT THE PREVIOUS line. Do the same in def CPprogress()
      If you don't want the utf-8 encoding, delete the four lines beginning with #STYLE#.

NOTE: If you want to copy lots of small files, the copy process for file is so fast
      that all you will see is a lot of lines scrolling in you terminal window - not enough time for a 'progress'.
      In that case, I use an overall progress that shows only one progress bar to the complete job.   nzX
'''
import os
import shutil
import sys
import threading
import time

######## COLORS ######
progressCOLOR = '\033[38;5;33;48;5;236m' #\033[38;5;33;48;5;236m# copy inside '' for colored progressbar| orange:#\033[38;5;208;48;5;235m
finalCOLOR =  '\033[38;5;33;48;5;33m' #\033[38;5;33;48;5;33m# copy inside '' for colored progressbar| orange:#\033[38;5;208;48;5;208m
#STYLE#BlueCOLOR = '\033[38;5;33m'#\033[38;5;33m# copy inside '' for colored progressbar Orange#'\033[38;5;208m'# # BG progress# #STYLE#
#STYLE#endBLOCK = '' # ▌ copy OR '' for none # BG progress# #STYLE# requires utf8 coding header
########

BOLD    = '\033[1m'
UNDERLINE = '\033[4m'
CEND    = '\033[0m'

def getPERCECENTprogress(source_path, destination_path):
    time.sleep(.24)
    if os.path.exists(destination_path):
        while os.path.getsize(source_path) != os.path.getsize(destination_path):
            sys.stdout.write('\r')
            percentagem = int((float(os.path.getsize(destination_path))/float(os.path.getsize(source_path))) * 100)
            steps = int(percentagem/5)
            copiado = int(os.path.getsize(destination_path)/1000000)# Should be 1024000 but this get's equal to Thunar file manager report (Linux - Xfce)
            sizzz = int(os.path.getsize(source_path)/1000000)
            sys.stdout.write(("         {:d} / {:d} Mb   ".format(copiado, sizzz)) +  (BOLD + progressCOLOR + "{:20s}".format('|'*steps) + CEND) + ("   {:d}% ".format(percentagem))) # BG progress
            #STYLE#sys.stdout.write(("         {:d} / {:d} Mb   ".format(copiado, sizzz)) +  (BOLD + BlueCOLOR + "▐" + "{:s}".format('█'*steps) + CEND) + ("{:s}".format(' '*(20-steps))+ BOLD + BlueCOLOR + endBLOCK+ CEND) +("   {:d}% ".format(percentagem))) #STYLE# # BG progress# closer to GUI but less compatible (no block bar with xterm) # requires utf8 coding header
            sys.stdout.flush()
            time.sleep(.01)

def CPprogress(SOURCE, DESTINATION):
    if os.path.isdir(DESTINATION):
        dst_file = os.path.join(DESTINATION, os.path.basename(SOURCE))
    else: dst_file = DESTINATION
    print(" ")
    print (BOLD + UNDERLINE + "FROM:" + CEND + "   "), SOURCE
    print (BOLD + UNDERLINE + "TO:" + CEND + "     "), dst_file
    print(" ")
    threading.Thread(name='progresso', target=getPERCECENTprogress, args=(SOURCE, dst_file)).start()
    shutil.copy2(SOURCE, DESTINATION)
    time.sleep(.02)
    sys.stdout.write('\r')
    sys.stdout.write(("         {:d} / {:d} Mb   ".format((int(os.path.getsize(dst_file)/1000000)), (int(os.path.getsize(SOURCE)/1000000)))) +  (BOLD + finalCOLOR + "{:20s}".format('|'*20) + CEND) + ("   {:d}% ".format(100))) # BG progress 100%
    #STYLE#sys.stdout.write(("         {:d} / {:d} Mb   ".format((int(os.path.getsize(dst_file)/1000000)), (int(os.path.getsize(SOURCE)/1000000)))) +  (BOLD + BlueCOLOR + "▐" + "{:s}{:s}".format(('█'*20), endBLOCK) + CEND) + ("   {:d}% ".format(100))) #STYLE# # BG progress 100%# closer to GUI but less compatible (no block bar with xterm) # requires utf8 coding header
    sys.stdout.flush()
    print(" ")
    print(" ")