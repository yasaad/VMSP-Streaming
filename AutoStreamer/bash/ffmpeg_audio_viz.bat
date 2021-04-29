"C:\Program Files\FFMPEG\ffmpeg.exe" ^
-hide_banner ^
-f dshow -i audio="Church Mics (Realtek(R) Audio)" ^
-af "pan=mono|c0=FL" ^
-filter_complex "showfreqs" ^
-f flv rtmp://x.rtmp.youtube.com/live2/ue2p-g79g-ysmk-6353-bhyy