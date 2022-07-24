ffmpeg.exe -i %1 -i meta_export.txt -map_metadata 1 -map_chapters 1 -codec copy "%~n1.cpy.%~X1" -y
pause