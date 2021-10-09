import datetime
import win32com.client
from enum import Enum
import win_task


### TODO: UNDERSTAND WEATHER OR NOT I WANT TO RUN WITH HIGHEST PRIVILEGE IN LINE 1058 of win_task.py

class Scheduler():

    class Trigger_frequency(Enum):
        ONE_TIME = 1
        DAILY = 2
        WEEKLY = 3


    def __init__(self):
        self.scheduler = win32com.client.Dispatch('Schedule.Service')
        self.scheduler.Connect()
        self.root_folder = self.scheduler.GetFolder('\Streaming')

    def print_tasks(self, XML=False):
        for task in self.root_folder.GetTasks(0):
            print(f'Name: "{task.Name}", Previous Runtime: {task.LastRunTime}, Next Runtime: {task.NextRunTime}')
            if XML:
                print(task.XML)
    
    def test_task_def(self, task_def):
        # Register Task
        # If task already exists, it will be updated
        TASK_CREATE_OR_UPDATE = 6
        # 0 for run when user is logged on and 1 for run when user is logged on or not
        TASK_LOGON_NONE = 0 
        self.root_folder.RegisterTaskDefinition(
            'Test Task', #Task Name
            task_def,
            TASK_CREATE_OR_UPDATE,
            'strea', #user
            'Jesusislord@33', #password
            TASK_LOGON_NONE
        )
    def create_new_task(self, name: str, start_time, action_path: str, action_arguments: str, trigger_frequency: Trigger_frequency):

        task_def = self.scheduler.NewTask(0)
        # trigger = task_def.Triggers.Create(0)

        #Repeat for a duration of number of days between
        # num_of_days = 10
        # trigger.Repetition.Duration = "P"+str(num_of_days)+"D"

        #use PT2M for every 2 minutes, use PT1H for every 1 hours
        # trigger.repetition.Interval = "PT2M"
        # trigger.StartBoundary = start_time.isoformat()

        # Create Action
        TASK_ACTION_EXEC = 0 
        action = task_def.Actions.Create(TASK_ACTION_EXEC)
        # action.ID = "TRIGGER BATCH"
        action.path = action_path
        action.Arguments = action_arguments

        # Set Parameters
        # task_def.RegistrationInfo.Description = "Test Task Description"
        # task_def.Settings.Enabled = True
        # task_def.Settings.StopIfGoingOnBatteries = False

        # Register Task
        # If task already exists, it will be updated
        TASK_CREATE_OR_UPDATE = 6
        # 0 for run when user is logged on and 1 for run when user is logged on or not
        TASK_LOGON_NONE = 0 
        self.root_folder.RegisterTaskDefinition(
            name, #Task Name
            task_def,
            TASK_CREATE_OR_UPDATE,
            'strea', #user
            'Jesusislord@33', #password
            TASK_LOGON_NONE
        )
LOCATION = '\Streaming'
USERNAME = 'strea'
PASSWORD = 'Jesusislord@33'
scheduler = Scheduler()
print(win_task.create_task(name="WIN_TASK_TEST9",
                           location=LOCATION,
                           cmd='echo',
                           user_name=USERNAME, 
                           password=PASSWORD, 
                           force=True,
                        #    force=True, cmd='echo "Hello"', 
                        #    description="Auto Generated Task Description", 
                        #    enabled=True,
                        #    trigger_type= "OnTaskCreation"
                           ))

# scheduler.print_tasks(XML=False)
start_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
action_path = "C:\\Users\\strea\\AppData\\Local\\ATEM Streamer\\ATEM Streamer.exe"
action_arguments = ""
scheduler.create_new_task("TEST2", start_time, action_path, action_arguments, scheduler.Trigger_frequency.DAILY)
print(win_task.list_tasks(LOCATION))