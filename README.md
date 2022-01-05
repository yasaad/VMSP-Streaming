# VMSP-Streaming

This is the streaming system for Virgin Mary and St. Pachomus Coptic Orthodox Church. There are two projects here. FFMPEG Streamer and ATEM Streamer. The fisrt is used to fully automate streaming using the Task Scheduler and FFMPEG. The second is a helper app to start the power swithc, youtube broadcast, and obs with the right title and thumbnail as well as handel closing all of the afformentioned in an easy to use GUI.

## FFMPEG Streamer

- run `start_streaming.py [Name of stream] [Hours to stream]` to start a stream
  - Usual Names
    - "Midnight Praises & Vespers"
    - "Divine Liturgy"
    - "Pascha"
      - running Pascha will automatically name the stream [Morning/Evening] of [Day of the Week] according to the time the stream runs

## ATEM Streamer

- To run any fbs commands first activate the virtual environment by running `.\Scripts\activate` in the "ATEM Streamer" Directory
  ```
  fbs clean
  fbs run
  fbs freeze (optionally --debug)
  fbs installer
  ```
- Installer is located at [ATEM StreamerSetup.exe](OBS%20Streamer/target/OBS%20StreamerSetup.exe)

- To run ATEM streamer from the command line use the following
```
"C:\Program Files (x86)\ATEM Streamer\ATEM Streamer.exe" 
```
with the following options
```
'-t', '--title' type=str Setting this will set the title, if it is also the name of a thumbnail it will set the thumbnail as well (thumbnail names listed below)
'-i', '--image' type=str Setting this will allow you to pick a default thumbnail even if your title is not the name of one of the thumbnails
Thumbnail Options: Divine Liturgy
                   Vespers & Midnight Praises
                   Bible Study
                   Palm Sunday
                   Holy Week
                   Coptic New Year
                   Feast of Nativity
                   Feast of Resurrection
                   Feast of the Cross
                   Feast of Theophany
                   Virgin Mary Revival
'-d', '--duration', type=float Auto turn off time in hours. After the set number of hours the stream will automatically stop (Ex 1.25 for 1 hour and 15 min)
'-u', '--unlisted' Use to make stream unlisted
'-a', '--autostart' Use to autostart stream
```
