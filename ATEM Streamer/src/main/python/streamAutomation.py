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
import PyATEMMax


from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

class StreamAutomation:
    """
    StreamAutomation class
    """
    def __init__(self, keys):
        self.OBS = None
        self.switcher = PyATEMMax.ATEMMax()
        self.switcher.connect("192.168.1.146")
        with open(f"{keys}/stream_key.txt") as f:
            self.STREAM_ID = f.readline()
            
        # Create Youtube Livestream
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = f"{keys}/client_secrets.json"
        credentials = None
        # Load credentials if authorized once
        if os.path.exists(f"{keys}/token.pickle"):
            with open(f"{keys}/token.pickle", "rb") as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
                credentials = flow.run_local_server(port=8080, authorization_prompt_message="Authorizing Account")
                with open(f"{keys}/token.pickle", "wb") as token:
                    pickle.dump(credentials, token)
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

    def setThumbnail(self, video_id, imagePath):
        # pylint: disable=maybe-no-member
        request = self.youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(imagePath)
        )
        response = request.execute()
        return response

    def checkForCurrentLiveStream(self):
        request = self.youtube.liveBroadcasts().list(
            part="id",
            broadcastStatus="active",
            broadcastType="all"
        )
        response = request.execute()
        items = response["items"]
        if len(items) > 0:
            return(response["items"][0]["id"])
        return None
    
    def checkBroadcastStatus(self, broadcast_id):
        # pylint: disable=maybe-no-member
        request = self.youtube.liveBroadcasts().list(
            part="snippet,contentDetails,status",
            prettyPrint=True,
            id=broadcast_id
        )
        response = request.execute()
        return(response["items"][0]["status"]["lifeCycleStatus"])
        

    def createBroadcast(self, title: str, public=True):
        start_time = datetime.now() + timedelta(hours=5)
        start_time = start_time.isoformat() + "Z"

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
        return response

    def deleteBroadcast(self, broadcast_id):
        # pylint: disable=maybe-no-member
        request = self.youtube.liveBroadcasts().delete(id=broadcast_id)
        response = request.execute()
        return(response)  

    def endBroadcast(self, broadcast_id):
        # pylint: disable=maybe-no-member
        status = self.checkBroadcastStatus(broadcast_id)
        if status != "live":
            return self.deleteBroadcast(broadcast_id)
        else:
            request = self.youtube.liveBroadcasts().transition(
                part="snippet,status",
                broadcastStatus="complete",
                id=broadcast_id
            )
            response = request.execute()
            return(response)  

    def turnOnPowerSwitch(self):
        # Turn power on
        
        switch = dlipower.PowerSwitch(hostname="192.168.1.33", userid="admin", password="1234")
        switch.on("Mixer")
        switch.on("ATEM")
        switch.on("Amp")
        while (switch.status("Amp") != "ON"):
            pass

    def cyclePower(self, outletName):
        switch = dlipower.PowerSwitch(hostname="192.168.1.33", userid="admin", password="1234")
        switch.cycle(outletName)
        
    def turnOffPowerSwitch(self):
        switch = dlipower.PowerSwitch(hostname="192.168.1.33", userid="admin", password="1234")

        switch.off("Mixer")
        switch.off("ATEM")
        switch.off("Amp")
    
    def startATEMStream(self):
        if self.switcher.waitForConnection(infinite=False):
            self.switcher.setMacroAction(self.switcher.atem.macros.macro8, self.switcher.atem.macroActions.runMacro)
            print("Started ATEM Stream")
        else:
            print("ERROR: no response from switcher")
            self.cyclePower("ATEM")
            

    def stopATEMStream(self):
        if self.switcher.waitForConnection(infinite=False):
            self.switcher.setMacroAction(self.switcher.atem.macros.macro5, self.switcher.atem.macroActions.runMacro)
            print("Stopped ATEM Stream")
        else:
            print("ERROR: no response from switcher")

    def closeATEMConnection(self):
        print("Closing ATEM Connection")
        self.switcher.disconnect() 
    
    def startOBS(self):
        if "obs64.exe" in (p.name() for p in psutil.process_iter()):
            os.system("taskkill /im obs64.exe /T /F >nul 2>&1")
            time.sleep(1)
        OBS_DIR = os.path.abspath(os.path.expanduser(r"C:\\Program Files\\obs-studio\\bin\\64bit\\"))
        OBS_CMD = r'obs64.exe --collection "VMSP Live Streaming" --profile "VMSP Church (autostream)" --scene "ATEM w/ Coptic Reader (Bottom Right)" --startstreaming'
        self.OBS = Popen(OBS_CMD, cwd=OBS_DIR, shell=True)

    def stopOBS(self):
        os.system("taskkill /im obs64.exe /T /F >nul 2>&1")
