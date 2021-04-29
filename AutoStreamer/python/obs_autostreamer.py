"""Auto streamer with obs"""
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
def write_to_file(message):
    """Logs history of livestreams to livestreams_ran.txt

    Args:
        message (str): Message to write with endline if wanted
    """
    with open(os.path.abspath("../docs/livestreams_ran.txt"), "a") as _f:
        _f.write(f"{message}")

def main(public):
    '''
    Turns on powerswitch ATEM, AMP, and MIXER
    Starts youtube broadcast with title and thumbnail
    Starts OBS stream on seperate process
    Runs for set time
    Stops youtube broadcast
    Stops OBS stream
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
    elif "Pascha" in args[1] or args[1] == "Covenant Thursday" or "Great Friday" in args[1]:
        thumbnail = "C:/Users/VMSP Church/Pictures/Thumbnails/Holy_Week.jpg"

    print("Starting Streaming to Youtube")
    os.system("taskkill /im obs64.exe /T /F >nul 2>&1")
    stream_automation.checkLiveStreamStatus()
    print("Turning on Power Switch")
    stream_automation.turnOnPowerSwitch()
    print("Creating Broadcast")
    broadcast_id = stream_automation.createBroadcast(video_title, public)
    stream_automation.setThumbnail(broadcast_id, thumbnail)
    stream_automation.bindBroadcast(broadcast_id)
    print("Starting OBS")
    stream_automation.startOBS()

    time.sleep(seconds)

    print("Ending Broadcast")
    stream_automation.endBroadcast(broadcast_id)
    print("Stopping OBS")
    stream_automation.stopOBS()
    print("Turning off Power Switch")
    stream_automation.turnOffPowerSwitch()

if __name__=="__main__":
    main(PUBLIC)