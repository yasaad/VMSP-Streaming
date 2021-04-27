CD "C:\Program Files\FFMPEG"
"C:\Program Files\FFMPEG\ffmpeg.exe" ^
-hide_banner ^
-threads:v 8 -threads:a 2 -filter_threads 2 ^
-thread_queue_size 1024 -format_code Hi59 -f decklink -vsync 1 -i "Intensity Pro" ^
-thread_queue_size 1024 -format_code Hp60 -raw_format "bgra" -f decklink -vsync 1 -i "Coptic Reader" ^
-filter_complex "[1]format=rgba,colorchannelmixer@CR=aa=0.8,scale@CR=iw/2.3:ih/2.3 [pip]; [0][pip] overlay@CR=0:main_h-overlay_h+1" ^
-f dshow -thread_queue_size 1024 -i audio="Church Mics (Realtek(R) Audio)" ^
-map 0:v -map 2:a ^
-pix_fmt yuv420p -c:v h264_nvenc -preset p4 -bf 4 ^
-g 59.94 ^
-b:v 4500K -maxrate 4500k -bufsize 5000k -b:a 128K ^
-af "pan=mono|c0=FL, arnndn=model=bd.rnnn" ^
-f flv rtmp://media2.smc-host.com:1935/vmspchurch.org/zoom1