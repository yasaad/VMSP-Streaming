# VMSP-Streaming
This is the streaming system for Virgin Mary and St. Pachomus Coptic Orthodox Church. There are two projects here. FFMPEG Streamer and OBS Streamer. The fisrt is used to fully automate streaming using the Task Scheduler and FFMPEG. The second is a helper app to start the power swithc, youtube broadcast, and obs with the right title and thumbnail as well as handel closing all of the afformentioned in an easy to use GUI.
## FFMPEG Streamer
- run ```start_streaming.py [Name of stream] [Hours to stream]``` to start a stream
  - Usual Names
    - "Midnight Praises & Vespers"
    - "Divine Liturgy"
    - "Pascha"
      - running Pascha will automatically name the stream [Morning/Evening] of [Day of the Week] according to the time the stream runs 

## OBS Streamer
- To run any fbs commands first activate the virtual environment by running ```.\Scripts\activate``` in the "OBS Streamer" Directory
  ```
  fbs clean
  fbs run
  fbs freeze (optionally --debug)
  fbs installer
  ```
- Frozen exe is located at "OBS Streamer\target\OBS Streamer.exe"
- Installer is located at "OBS Streamer\target
