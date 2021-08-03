### Reasons for chapter-ridge

This script takes the favorites menu of [mpc-be](https://sourceforge.net/projects/mpcbe/) Videoplayer as a Editor (or source) for writing the chapters to the mp4 files.

The Benefits:
- easy editing with mpc-be Player at the moment when you play
- you can jump more easy in the seekbar
- chapters get visible in other players/computers too
- the script generates a excel file where you can also put more paths etc.
- speed is improved to write all chapters per file together, files will updated by timestamp (newest first)
- careful mode: Decide each file whether to process and afterwards whether to apply changes
- tolerance of one second to avoid duplicates / autoinit a starting chapter
- the data is available as excel file so you could import / reuse it
### Install

- ffmpeg and ffprobe https://ffmpeg.org/download.html#build-windows
- install all dependecies of this project in your envoirement
- put the ffmpeg path in the mpcbe.py
- backup or create a trial folder
- run the script

### TODO / limitations
- find the ffmpeg path better
- commandline parameters
- make it available not only for windows (where to read favs from?)
- option for mapping paths
- chapters for PotPlayer
- simulate mode
- tidyup librarys
- make a config (path ffmpeg, behavoiur copying, mapping)
- check for enough space for copying
- index the files and copy chapter back to mp4
- add progress bar for copying files: https://github.com/althonos/ffpb/issues

### other sources

- https://github.com/cbitterfield/chaptermarkers/blob/main/chaptermarkers/chaptermarkers.py
- https://ikyle.me/blog/2020/add-mp4-chapters-ffmpeg