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

def write_to_file(message):
    """Logs history of livestreams to livestreams_ran.txt

    Args:
        message (str): Message to write with endline if wanted
    """
    with open("C:/VMSP Streaming/FFMPEG Streamer/docs/livestreams_ran.txt", "a") as _f:
        _f.write(f"{message}")

def stop_ffmpeg_power_switch(ffmpeg_pipe, process, stream, start_time):
    """Closes FFMPEG and turns off power switch"""
    print("Stopping FFMPEG")
    ffmpeg_pipe.send("q")
    process.join()
    print("Turining off powerswitch")
    stream.turnOffPowerSwitch()
    write_to_file(f"From {start_time} - {datetime.now().strftime('%H:%M')}\n")


def ffmpeg(command, connection, file_write):
    '''FFMPEG process for handeling stdin, stdout, and stderr of FFMPEG'''
    def handle_input(connection, process, write):
        if connection.poll():
            arg_to_pass = connection.recv()
            print("FROM FFMPEG", arg_to_pass)
            write(f"Sending Command:j {arg_to_pass}")
            process.stdin.write(arg_to_pass.encode())
            process.stdin.flush()
            if arg_to_pass == "q":
                process.terminate()
                return 0
        return 1

    ffmpeg_stream = Popen(
        command, cwd=r"C:\\Program Files\\FFMPEG", stdin=PIPE, stdout=PIPE, stderr=STDOUT
    )
    line = ""
    delimeters = {"\n", "\r"}
    # wait until streaming starts
    try:
        for char in iter(lambda: ffmpeg_stream.stdout.read(1), ""):
            char = char.decode()
            if char in delimeters:
                if "error" in line.lower():
                    file_write(line)
                    print(line)
                    ffmpeg_stream.terminate()
                    connection.send(-1)
                    raise SystemError(line)
                if "frame=" in line:
                    print("Started Streaming...")
                    connection.send(1)
                    break
                print(line, end=char)
                line = ""
            else:
                line += char

        for char in iter(lambda: ffmpeg_stream.stdout.read(1), ""):
            if handle_input(connection, ffmpeg_stream, file_write) == 0:
                return
            char = char.decode()
            if char in delimeters:
                print(line, end=char)
                line = ""
            else:
                line += char
    except KeyboardInterrupt:
        file_write("FFMPEG Keyboard interupt: Stopping\n")
        ffmpeg_stream.communicate('q'.encode())
        ffmpeg_stream.terminate()

def main(public, nile, bottom_left):
    '''
    Turns on powerswitch ATEM, AMP, and MIXER
    Starts youtube broadcast with title and thumbnail
    Starts FFMPEG stream on seperate process
    Runs for set time
    Stops youtube broadcast
    Stops FFMPEG stream
    Turns off powerswitch ATEIM, AMP, and MIXER
    '''
    args = sys.argv
    if len(args) < 3:
        raise ValueError("Please have service name and hours to stream as arguments")
    if len(args) == 4:
        if args[3].lower() == "true":
            public = True
        elif args[3].lower() == "false":
            public = False
        else:
            print("3rd argument (optional) must be either True or False")
            sys.exit(2)
    print(f"Starting {'Public' if public else 'Unlisted'} stream")
    stream_automation = StreamAutomation(os.path.abspath("../keys"))
    service_date = date.strftime(date.today(), "%m/%d/%Y")
    service_name = args[1]
    if service_name == "Pascha":
        if int(datetime.now().strftime("%H")) < 12:
            # Day of current day
            day = calendar.day_name[date.today().weekday()]
            service_name = f"Day of {day} Pascha"
        else:
            # Eve of next day=]
            day = calendar.day_name[date.today().weekday() + 1]
            service_name = f"Eve of {day} Pascha"

    seconds = int(float(args[2]) * 3600)
    video_title = f"{service_name} - {service_date}"

    start_time = datetime.now().strftime("%H:%M")
    write_to_file(f"{video_title}: ")
    print(f"{video_title} will stream for {seconds/3600} hours")
    thumbnail = "C:/Users/VMSP Church/Pictures/Thumbnails/Divine_Liturgy.jpg"
    tesbeha = False
    if "Vespers" in service_name:
        thumbnail = "C:/Users/VMSP Church/Pictures/Thumbnails/Midnight_Praises.jpg"
        tesbeha = True
    elif "Pascha" in args[1] or args[1] == "Covenant Thursday":
        thumbnail = "C:/Users/VMSP Church/Pictures/Thumbnails/Holy_Week.jpg"

    print("Starting Streaming to Youtube")
    os.system("taskkill /im obs64.exe /T /F >nul 2>&1")
    stream_automation.checkLiveStreamStatus()
    stream_automation.turnOnPowerSwitch()
    broadcast_id = stream_automation.createBroadcast(video_title, public)
    stream_automation.setThumbnail(broadcast_id, thumbnail)
    stream_automation.bindBroadcast(broadcast_id)

    # Start FFMPEG Streaming
    print("Starting Stream")
    stream_address = "-f flv rtmp://media2.smc-host.com:1935/vmspchurch.org/zoom1"
    location = "main_w-overlay_w:main_h-overlay_h+1"
    if not nile:
        stream_address = (
            "-f flv rtmp://x.rtmp.youtube.com/live2/ue2p-g79g-ysmk-6353-bhyy"
        )
    if bottom_left:
        location = "0:main_h-overlay_h+1"

    #add arnndn=model=bd.rnnn to the -af for noise reduction
    cmd = (
        r'"C:\\Program Files\\FFMPEG\\ffmpeg.exe"'
        + " -hide_banner"
        + " -threads:v 8 -threads:a 2 -filter_threads 2"
        + ' -thread_queue_size 1024 -format_code Hi59 -timestamp_align 0'
        + ' -f decklink -video_pts wallclock -audio_pts wallclock -i "Intensity Pro"'
        + ' -thread_queue_size 1024 -format_code Hp60 -raw_format "bgra" -timestamp_align 0'
        + ' -f decklink -video_pts wallclock -audio_pts wallclock -i "Coptic Reader"'
        + ' -filter_complex'
        + ' "[1]format=rgba,'
        + 'colorchannelmixer@CR=aa=0.8,'
        + 'scale@CR=iw/2.3:ih/2.3,'
        + 'setpts=PTS-STARTPTS [pip];'
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
    ffmpeg_process = Process(target=ffmpeg, args=(cmd, child_conn, write_to_file))
    ffmpeg_process.start()
    #ffmpeg failed for some reason
    if ffmpeg_conn.recv() != 1:
        stream_automation.deleteBroadcast(broadcast_id)
        stop_ffmpeg_power_switch(ffmpeg_conn, ffmpeg_process, stream_automation, start_time)
        sys.exit(2)

    if nile:
        print("Starting Nile Stream")
        startNileStream()
    try:
        if (tesbeha and seconds > 45*60):
            # change overlay after 45 min
            time.sleep(45*60)
            print("Setting filters for tesbeha")
            ffmpeg_conn.send(
                'cscale@CR -1 w iw\n' \
                + 'cscale@CR -1 h ih\n' \
                + 'ccolorchannelmixer@CR -1 aa 0.75\ncoverlay@CR -1 y 0\n'
                )
            time.sleep(seconds - 45*60)
        else:
            time.sleep(seconds)

        print("Sending q")
        ffmpeg_conn.send("q")
        ffmpeg_process.join()
        # complete broadcast
        status = stream_automation.checkBroadcastStatus(broadcast_id)
        print("BROADCAST STATUS:", status)
        if status != "live":
            print("Deleting stream")
            stream_automation.deleteBroadcast(broadcast_id)
        else:
            print("Ending Broadcast")
            stream_automation.endBroadcast(broadcast_id)
        stop_ffmpeg_power_switch(ffmpeg_conn, ffmpeg_process, stream_automation, start_time)

    except KeyboardInterrupt:
        stop_live_stream = input("\nDo you want to stop the Youtube Broadcast as well? (y/N) ")\
            .lower().strip() == 'y'
        if stop_live_stream:
            if status != "live":
                stream_automation.deleteBroadcast(broadcast_id)
            else:
                stream_automation.endBroadcast(broadcast_id)
            stop_ffmpeg_power_switch(ffmpeg_conn, ffmpeg_process, stream_automation, start_time)
        else:
            ffmpeg_conn.send("q")
            ffmpeg_process.join()
            print("Stopped FFMPEG but did not stop Youtube Broadcast")
    except SystemError:
        stream_automation.deleteBroadcast(broadcast_id)
        stop_ffmpeg_power_switch(ffmpeg_conn, ffmpeg_process, stream_automation, start_time)

if __name__ == "__main__":
    main(PUBLIC, NILE, BOTTOM_LEFT)
