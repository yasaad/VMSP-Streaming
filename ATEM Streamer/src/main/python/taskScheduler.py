import datetime
import win32com.client

scheduler = win32com.client.Dispatch('Schedule.Service')
scheduler.Connect()
root_folder = scheduler.GetFolder('\Streaming')
task_def = scheduler.NewTask(0)

# Defining the Start time of job
start_time = datetime.datetime.now() + datetime.timedelta(minutes=1)

#For Daily Trigger set this variable to 2; for One time run set this value as 1
TASK_TRIGGER = 1
trigger = task_def.Triggers.Create(TASK_TRIGGER)

#Repeat for a duration of number of days between
num_of_days = 10
# trigger.Repetition.Duration = "P"+str(num_of_days)+"D"

#use PT2M for every 2 minutes, use PT1H for every 1 hours
# trigger.repetition.Interval = "PT2M"
trigger.StartBoundary = start_time.isoformat()

# Create Action
TASK_ACTION_EXEC = 0 
action = task_def.Actions.Create(TASK_ACTION_EXEC)
action.ID = "TRIGGER BATCH"
action.path = "C:\\Users\\strea\\AppData\\Local\\ATEM Streamer\\ATEM Streamer.exe"
action.Arguments = ""

# Set Parameters
task_def.RegistrationInfo.Description = "Test Task Description"
task_def.Settings.Enabled = True
task_def.Settings.StopIfGoingOnBatteries = False

# Register Task
# If task already exists, it will be updated
TASK_CREATE_OR_UPDATE = 6
# 0 for run when user is logged on and 1 for run when user is logged on or not
TASK_LOGON_NONE = 0 
root_folder.RegisterTaskDefinition(
    'Test Task', #Task Name
    task_def,
    TASK_CREATE_OR_UPDATE,
    'strea', #user
    'Jesusislord@33', #password
    TASK_LOGON_NONE
)
