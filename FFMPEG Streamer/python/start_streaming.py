"""Auto streamer with ffmpeg
"""
import os
import sys
from multiprocessing import Process, Pipe
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime, date
import calendar
import time
from streamAutomation import StreamAutomation
from nile_stream import startNileStream

PUBLIC = True
NILE = False
BOTTOM_LEFT = True


def stop_ffmpeg_power_switch():
    """Closes FFMPEG and turns off power switch"""
    print("Turining off powerswitch")
    streamAutomation.turnOffPowerSwitch()
    write_to_file(f"From {startTime} - {datetime.now().strftime('%H:%M')}\n")


def ffmpeg(cmd, connection):
    def handle_input(connection, process):
        if connection.poll():
            arg_to_pass = connection.recv()
            print("FROM FFMPEG", arg_to_pass)
            ffmpeg_stream.stdin.write(arg_to_pass.encode())
            ffmpeg_stream.stdin.flush()
            if arg_to_pass == "q":
                ffmpeg_stream.terminate()
                return 0
        return 1

    ffmpeg_stream = Popen(
        cmd, cwd=r"C:\\Program Files\\FFMPEG", stdin=PIPE, stdout=PIPE, stderr=STDOUT
    )
    line = ""
    delimeters = {"\n", "\r"}
    # wait until streaming starts
    for ch in iter(lambda: ffmpeg_stream.stdout.read(1), ""):
        ch = ch.decode()
        if ch in delimeters:
            if "error" in line.lower():
                print(line)
                ffmpeg_stream.terminate()
                raise SystemError(line)
            if "frame=" in line:
                print("Started Streaming...")
                break
            print(line, end=ch)
            line = ""
        else:
            line += ch

    for ch in iter(lambda: ffmpeg_stream.stdout.read(1), ""):
        if handle_input(connection, ffmpeg_stream) == 0:
            return
        ch = ch.decode()
        if ch in delimeters:
            print(line, end=ch)
            line = ""
        else:
            line += ch


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        raise ValueError("Please have service name and hours to stream as arguments")
    streamAutomation = StreamAutomation()
    service_date = date.strftime(date.today(), "%m/%d/%Y")
    service_name = args[1]
    if service_name == "Pascha":
        if int(datetime.now().strftime("%H")) < 12:
            # Day of current day
            day = calendar.day_name[date.today().weekday()]
            service_name = f"Day of {day} Pascha"
        else:
            # Eve of next day
            day = calendar.day_name[date.today().weekday() + 1]
            service_name = f"Eve of {day} Pascha"

    seconds = int(float(args[2]) * 3600)
    video_title = f"{service_name} - {service_date}"

    def write_to_file(message):
        """Logs history of livestreams to livestreams_ran.txt

        Args:
            message (str): Message to write with endline if wanted
        """
        with open("C:/VMSP Streaming/FFMPEG Streamer/docs/livestreams_ran.txt", "a") as _f:
            _f.write(f"{message}")

    startTime = datetime.now().strftime("%H:%M")
    write_to_file(f"{video_title}: ")
    print(f"{video_title} will stream for {seconds/3600} hours")
    thumbnail = "C:/Users/VMSP Church/Pictures/Thumbnails/Divine_Liturgy.jpg"
    tesbeha = False
    if "Vespers" in service_name:
        thumbnail = "C:/Users/VMSP Church/Pictures/Thumbnails/Midnight_Praises.jpg"
        tesbeha = True
    elif "Pascha" in args[1]:
        thumbnail = "C:/Users/VMSP Church/Pictures/Thumbnails/Holy_Week.jpg"

    print("Starting Streaming to Youtube")
    os.system("taskkill /im obs64.exe /T /F >nul 2>&1")
    streamAutomation.checkLiveStreamStatus()
    streamAutomation.turnOnPowerSwitch()
    broadcast_id = streamAutomation.createBroadcast(video_title, PUBLIC)
    streamAutomation.setThumbnail(broadcast_id, thumbnail)
    streamAutomation.bindBroadcast(broadcast_id)

    # Start FFMPEG Streaming
    print("Starting Stream")
    stream_address = "-f flv rtmp://media2.smc-host.com:1935/vmspchurch.org/zoom1"
    location = "main_w-overlay_w:main_h-overlay_h+1"
    if not NILE:
        stream_address = (
            "-f flv rtmp://x.rtmp.youtube.com/live2/ue2p-g79g-ysmk-6353-bhyy"
        )
    if BOTTOM_LEFT:
        location = "0:main_h-overlay_h+1"

    #add arnndn=model=bd.rnnn to the -af for noise reduction
    cmd = (
        r'"C:\\Program Files\\FFMPEG\\ffmpeg.exe"'
        + " -hide_banner"
        + " -threads:v 8 -threads:a 2 -filter_threads 2"
        + ' -thread_queue_size 1024 -format_code Hi59 -timestamp_align 0 -f decklink -i "Intensity Pro"'
        + ' -thread_queue_size 1024 -format_code Hp60 -raw_format "bgra" -timestamp_align 0 -f decklink -i "Coptic Reader"'
        + ' -filter_complex "[1]format=rgba,colorchannelmixer@CR=aa=0.8,scale@CR=iw/2.3:ih/2.3,setpts=PTS-STARTPTS [pip];'
        + f' [0][pip] overlay@CR={location},setpts=PTS-STARTPTS"'
        + ' -f dshow -thread_queue_size 1024 -i audio="Church Mics (Realtek(R) Audio)"'
        + " -map 0:v -map 2:a"
        + " -pix_fmt yuv420p -c:v h264_nvenc -preset p4 -bf 4"
        + " -g 59.94"
        + " -b:v 4500K -maxrate 4500k -bufsize 5000k -b:a 128K"
        + ' -af "pan=mono|c0=FL"'
        + f" {stream_address}"
    )

    print("Command:\n", cmd)

    ffmpeg_conn, child_conn = Pipe()
    ffmpeg_process = Process(target=ffmpeg, args=(cmd, child_conn))
    ffmpeg_process.start()
    # except KeyboardInterrupt:
    #     stopLiveStream = input("Do you want to stop the Youtube Broadcast as well? (y/N) ").lower().strip() == 'y'
    #     if stopLiveStream:
    #         streamAutomation.endBroadcast(broadcast_id)
    #         stop_ffmpeg_power_switch()
    #     else:
    #         ffmpeg_stream.communicate(input=b"q")
    #         time.sleep(1)
    #         ffmpeg_stream.terminate()
    #         ffmpeg_stream.kill()
    #         print("Stopped FFMPEG but did not stop Youtube Broadcast")
    # except SystemError:
    #     streamAutomation.deleteBroadcast(broadcast_id)
    #     stop_ffmpeg_power_switch()

    # if NILE:
    #     print("Starting Nile Stream")
    #     startNileStream()
    # # change overlay after 45 min
    # if (tesbeha and seconds > 45*60):
    #     time.sleep(45*60)
    #     print("Setting filters for tesbeha")
    #     ffmpeg_stream.stdin.write(b'cscale@CR -1 w iw\ncscale@CR -1 h ih\nccolorchannelmixer@CR -1 aa 0.75\ncoverlay@CR -1 y 0\n')
    #     ffmpeg_stream.stdin.flush()
    #     print("Commands sent, sleeping...")
    #     time.sleep(seconds - 45*60)
    # else:
    time.sleep(seconds)
    # print("Sending c")
    # ffmpeg_conn.send(
    #     "cscale@CR -1 w iw\ncscale@CR -1 h ih\nccolorchannelmixer@CR -1 aa 0.75\ncoverlay@CR -1 y 0\n"
    # )
    # time.sleep()
    print("Sending q")
    ffmpeg_conn.send("q")
    ffmpeg_process.join()
    print("FFMPEG joined")
    # complete broadcast
    streamAutomation.endBroadcast(broadcast_id)
    stop_ffmpeg_power_switch()
    print("Program Done")
