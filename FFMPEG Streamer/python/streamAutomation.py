"""
Stream automation class for starting auto stream
"""
import os
import time
import psutil
from subprocess import Popen
from datetime import datetime, timedelta
import pickle
import dlipower


from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

class StreamAutomation:
    """
    StreamAutomation class
    """
    def __init__(self):
        self.OBS = None
        with open("C:/VMSP Streaming/FFMPEG Streamer/keys/stream_key.txt") as f:
            self.STREAM_ID = f.readline()
            
        # Create Youtube Livestream
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secrets.json"
        credentials = None
        # Load credentials if authorized once
        if os.path.exists("C:/VMSP Streaming/FFMPEG Streamer/keys/token.pickle"):
            print("Loading Credentials From File...")
            with open("C:/VMSP Streaming/FFMPEG Streamer/keys/token.pickle", "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("Refreshing Access Token...")
                credentials.refresh(Request())
            else:
                print("Fetching New Token...")
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
                credentials = flow.run_local_server(port=8080, authorization_prompt_message="Authorizing Account")
                with open("C:/VMSP Streaming/FFMPEG Streamer/keys/token.pickle", "wb") as token:
                    print("Saving Credentials for Future Use...")
                    pickle.dump(credentials, token)
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

    def setThumbnail(self, video_id, imagePath):
        # pylint: disable=maybe-no-member
        print("THUMBNAIL: ", imagePath)
        request = self.youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(imagePath)
        )
        response = request.execute()
        return response

    def checkBroadcastStatus(self, broadcast_id):
        # pylint: disable=maybe-no-member
        request = self.youtube.liveBroadcasts().list(
            part="snippet,contentDetails,status",
            prettyPrint=True,
            id=broadcast_id
        )
        response = request.execute()
        print("Broadcast Status:")
        print(response["items"][0]["snippet"]["title"])
        print(response["items"][0]["status"])
        return(response["items"][0]["status"])

    def createBroadcast(self, title: str, public=True):
        start_time = datetime.now() + timedelta(hours=5)
        start_time = start_time.isoformat() + "Z"
        print("Starting Stream to Youtube")

        # pylint: disable=maybe-no-member
        request = self.youtube.liveBroadcasts().insert(
            part="snippet,contentDetails,status",
            prettyPrint=True,
            body={
                "contentDetails": {
                "enableClosedCaptions": True,
                "enableContentEncryption": True,
                "enableDvr": True,
                "enableEmbed": True,
                "enableAutoStart": True,
                "recordFromStart": True,
                "startWithSlate": False
                },
                "snippet": {
                    "title": title,
                    "description": "#VMSP #VMSPChurch #Pachomius",
                    "scheduledStartTime": start_time
                },
                "status": {
                "privacyStatus": "public" if public else "unlisted",
                "selfDeclaredMadeForKids": False
                }
            }
        )

        response = request.execute()
        return response["id"]

    def bindBroadcast(self, broadcast_id):
        # pylint: disable=maybe-no-member
        print("BINDING TO STREAM:", self.STREAM_ID)
        request = self.youtube.liveBroadcasts().bind(
            id=broadcast_id,
            part="snippet",
            streamId=self.STREAM_ID
        )
        response = request.execute()
        return response

    def checkLiveStreamStatus(self, stream_id=True):
        # pylint: disable=maybe-no-member
        request = self.youtube.liveStreams().list(
            part="snippet,cdn,contentDetails,status",
            id = self.STREAM_ID
        ) if stream_id else self.youtube.liveStreams.list(
            part="snippet,cdn,contentDetails,status",
            mine=True

        )
        response = request.execute()
        for item in response['items']:
            print(f"Livestream Status of {item['snippet']['title']}: {item['status']['streamStatus']}")
        return response

    def deleteBroadcast(self, broadcast_id):
        # pylint: disable=maybe-no-member
        request = self.youtube.liveBroadcasts().delete(id=broadcast_id)
        response = request.execute()
        print(response)
        return(response)  

    def endBroadcast(self, broadcast_id):
        # pylint: disable=maybe-no-member
        request = self.youtube.liveBroadcasts().transition(
            broadcastStatus="complete",
            id=broadcast_id,
            part="snippet,status"
        )
        response = request.execute()
        print(response)
        return(response)  

    def turnOnPowerSwitch(self):
        # Turn power on
        print('Connecting to DLI powerSwitch')
        
        switch = dlipower.PowerSwitch(hostname="192.168.1.33", userid="admin", password="1234")
        # Turn on Mixer
        print("Turning Mixer ON")
        switch.on("Mixer")
        # Turn on ATEM
        print("Turning ATEM ON")
        switch.on("ATEM")
        # Turn on Amp
        print("Turning AMP ON")
        switch.on("Amp")
        while (switch.status("Amp") != "ON"):
            pass

    def turnOffPowerSwitch(self):
        switch = dlipower.PowerSwitch(hostname="192.168.1.33", userid="admin", password="1234")

        print("Turning Mixer OFF")
        switch.off("Mixer")
        # Turn on ATEM
        print("Turning ATEM OFF")
        switch.off("ATEM")
        # Turn on Amp
        print("Turning AMP OFF")
        switch.off("Amp")

    def startOBS(self):
        if "obs64.exe" in (p.name() for p in psutil.process_iter()):
            print("Closing any existing OBS windows")
            os.system("taskkill /im obs64.exe /T /F >nul 2>&1")
            time.sleep(1)
        print("Opening OBS")
        OBS_DIR = os.path.abspath(os.path.expanduser(r"C:\\Program Files\\obs-studio\\bin\\64bit\\"))
        OBS_CMD = r'obs64.exe --collection "VMSP Live Streaming" --profile "VMSP Church (autostream)" --scene "ATEM w/ Coptic Reader (Bottom Right)" --startstreaming'
        self.OBS = Popen(OBS_CMD, cwd=OBS_DIR, shell=True)

    def stopOBS(self):
        os.system("taskkill /im obs64.exe /T /F >nul 2>&1")
