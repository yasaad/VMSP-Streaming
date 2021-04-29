import os, sys, signal
from subprocess import Popen, PIPE, STDOUT
import time

'cscale@CR -1 w iw\ncscale@CR -1 h ih\nccolorchannelmixer@CR -1 aa 0.7\ncoverlay@CR -1 y 0\n'.encode(encoding="utf-8", errors="ignore")
try:
    cmd = '"C:\Program Files\FFMPEG\\ffmpeg.exe"' \
        + ' -hide_banner' \
        + ' -threads:v 8 -threads:a 2 -filter_threads 2' \
        + ' -thread_queue_size 1024 -format_code Hi59 -f decklink -vsync 1 -i "Intensity Pro"' \
        + ' -thread_queue_size 1024 -format_code Hp60 -raw_format "bgra" -f decklink -vsync 1 -i "Coptic Reader"' \
        + ' -filter_complex "[1]format=rgba,colorchannelmixer@CR=aa=0.8,scale@CR=iw/2.3:ih/2.3 [pip]; [0][pip] overlay@CR=main_w-overlay_w:main_h-overlay_h+1"' \
        + ' -f dshow -thread_queue_size 1024 -i audio="Church Mics (Realtek(R) Audio)"' \
        + ' -map 0:v -map 2:a' \
        + ' -pix_fmt yuv420p -c:v h264_nvenc -preset p4 -bf 4' \
        + ' -g 59.94' \
        + ' -b:v 4500K -maxrate 4500k -bufsize 5000k -b:a 128K' \
        + ' -af "pan=mono|c0=FL"' \
        + ' -f flv rtmp://media2.smc-host.com:1935/vmspchurch.org/zoom1'
    print(cmd)
    # test = Popen('ffplay -f dshow -i video="Logitech Webcam C930e', cwd=".", stdin=PIPE, stdout=PIPE, text=True)
    ffmpeg_stream = Popen(cmd, cwd=r"C:\\Program Files\\FFMPEG", stdin=PIPE, stdout=PIPE, stderr=STDOUT, bufsize=10**8)
except:
    e = sys.exc_info()[0]
    print(f"Error: {e}")

print("HERHERHERHERH", ffmpeg_stream.stdout, ffmpeg_stream.stderr)
line = ""
delimeters = {'\n', '\r'}
for ch in iter(lambda: ffmpeg_stream.stdout.read(1), ""):
    ch = ch.decode()
    if ch in delimeters:
        if line != '':
            if "frame=" in line:
                print("Started Streaming")
                break
            print(line)
        line = ""
    else:
        line += ch
# for line in ffmpeg_stream.stdout:
#     line = line.decode()
#     print(line, end='')
#     if "error" in line:
#         raise Exception(line)
#     if 'frame=' in line:
#         break
time.sleep(5)
# ffmpeg_stream.stdin.write('c'.encode("GBK"))
print("Sending commands")
ffmpeg_stream.stdin.write(b'cscale@CR -1 w iw\ncscale@CR -1 h ih\nccolorchannelmixer@CR -1 aa 0.7\ncoverlay@CR -1 y 0\n')
ffmpeg_stream.stdin.flush()
print("Commands sent, sleeping...")
ffmpeg_stream.stdout.readuntil(b'Enter')
for ch in iter(lambda: ffmpeg_stream.stdout.read(1), ""):
    ch = ch.decode()
    if ch in delimeters:
        if line != '':
            # if "frame=" in line:
            #     print("Started Streaming")
            #     break
            print(line)
        line = ""
    else:
        line += ch
# ffmpeg_stream.communicate(input=b"cscale@CR -1 w iw\ncscale@CR -1 h ih\n", timeout=3)
# ffmpeg_stream.communicate(input=b"cscale@CR -1 h ih\n")
# ffmpeg_stream.communicate(input=b"ccolorchannelmixer@CR -1 aa 0.7\n")
time.sleep(5)
ffmpeg_stream.communicate(input=b"q")
ffmpeg_stream.terminate()

