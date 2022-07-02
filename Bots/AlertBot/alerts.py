#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 21:40:32 2020

@author: alberto

Implement periodic reminders. For example
    monday 20:00 (every monday)
    6 12:00 (every 6th day of the month)
            
"""

import datetime
from threading import Thread, Event
import dropbox

'''Implement reminders for week-day and month-day.'''

'''For periodic reminders, save in the a file the input text string and the
last time the reminder went off (or the time when it was originally set).'''

'''For single-time reminders, save in a external file only the time when the reminder
has to be sent.'''

'''Store in the external files (format .log, for example) the string obtained from the
method .isoformat() of a datetime.datetime object.'''

# fileAlerts = 'single_alerts.log'
# filePeriodic = 'periodic_alerts.log'

class WrongTimeFormat(Exception):
    '''An exception that will be raised when the script is unable to read the time
    given.'''
    pass

class WrongTimeInterval(Exception):
    '''An exception that will be raised when parsing something that is not a correct
    time interval.'''
    pass

class NoTimeBackup(Exception):
    '''An exception that will be raised when the first element in the FILE_ALERTS
    is not a datetime.datetime (the moment of the next backup).'''
    pass

class myTimer(Thread):
    '''Implemented based on a response of
    https://stackoverflow.com/questions/9812344/cancellable-threading-timer-in-python'''
    def __init__(self, func, wait_seconds = 1, args = ()):
        ''' func: the function that is going to be run periodically.
            wait_seconds: the amount of seconds to wait between executions of func.
            args: arguments passed to the function.'''
        self.func = func
        self.wait_seconds = wait_seconds
        self.args = args
        
        # Create a thread.
        Thread.__init__(self)
        # Create an event flag. When it is set, we will stop the execution of the thread.
        self.event = Event()
        # Counter variable
        self.count = 10

    def run(self):
        '''The process that will be executed when calling the .start() method,
        inherited from the threading.Thread class.
        https://docs.python.org/3/library/threading.html'''
        # If the event flag is not set, run the process.
        while not self.event.is_set():
            # Run the function, with arguments if there are any.
            self.func(*self.args)
            # Wait before running the function again.
            self.event.wait(self.wait_seconds)

    def stop(self):
        '''When the stop method is called, set the event flag, that will stop
        the execution of the run() method.'''
        self.event.set()


def parseTimeInterval(string):
    '''Get a datetime.deltatime object from a string, written as for example
        1y2mo3w4d5h6m    
    Look for: 
        years (y) -> months (mo) -> weeks (w) -> days (d) -> hours (h) -> minutes (m)
    '''
    years = 0
    months = 0
    weeks = 0
    days = 0
    hours = 0
    minutes = 0
    try:
        split = string.split('y')
        if len(split) == 2:
            years = int(split[0])
            string = split[1]
            
        split = string.split('mo')
        if len(split) == 2:
            months = int(split[0])
            string = split[1]
            
        split = string.split('w')
        if len(split) == 2:
            weeks = int(split[0])
            string = split[1]
        
        split = string.split('d')
        if len(split) == 2:
            days = int(split[0])
            string = split[1]
            
        split = string.split('h')
        if len(split) == 2:
            hours = int(split[0])
            string = split[1]
            
        split = string.split('m')
        if len(split) == 2:
            minutes = int(split[0])
            string = split[1]
        
        # print('Yers: {}\nMonths: {}\nWeeks: {}\nDays: {}\nHours: {}\nMinutes: {}'.format(
        #     years, months, weeks, days, hours, minutes))
        
        # Compute the total interval of time
        timedelta = datetime.timedelta(days = days + 7*weeks + 31*months + 365*years, 
                                  hours=hours, minutes=minutes)
        # If the total interval of time is null, raise an exception
        if timedelta.total_seconds() == 0:
            raise WrongTimeInterval
        return datetime.datetime.now() + timedelta

    except:
        raise WrongTimeInterval
        return
    
    
def parseInputAlert(inputSplit):
    '''Separate an input string, already splitted by spaces, in a datetime object
    with the moment when the alert should go off and the text of the alert.'''
    
    # Try to parse the first element as a time interval
    try:
        timeTarget = parseTimeInterval(inputSplit[1])
        # Try to parse the third element as an exact hour
        try:
            # Split the third object as hour:minute
            hour, minute = inputSplit[2].split(':')
            # Modify the hour and minute of the datetime.datetime object
            timeTarget = timeTarget.replace(hour=int(hour), minute=int(minute))
            # The text of the alert is given by the following words
            return timeTarget, ' '.join(inputSplit[3:])
        # The above will raise an exception in two cases:
            # Impossible to unpack inputSplit[2].split(':') in two values
            # Impossible to convert hour and minute to integers
        except:
            # The text of the alert is given by the following words
            return timeTarget, ' '.join(inputSplit[2:])
        
    except WrongTimeInterval:
        # Initialize the timeTarget as the current time, which will be modified later
        timeTarget = datetime.datetime.now()
        
        # Try to parse the 2nd element as an exact day
        try:
            # Split the 2nd element
            exactDay = inputSplit[1].split('/')
            # There are two options: DD/MM/YY or DD/MM
            timeTarget = timeTarget.replace(day=int(exactDay[0]), month=int(exactDay[1]))
            if len(exactDay) == 3:
                # Modify also the year
                timeTarget = timeTarget.replace(year=(int(exactDay[2]) + 2000)%2000 + 2000)
            
            # Try to parse the 3rd element as an exact hour:minute
            try:
                # Split the third object as hour:minute
                hour, minute = inputSplit[2].split(':')
                # Modify the hour and minute of the datetime.datetime object
                timeTarget = timeTarget.replace(hour=int(hour), minute=int(minute))
                # The text of the alert is given by the following words
                return timeTarget, ' '.join(inputSplit[3:])
            # The above will raise an exception if the hour:minute is not correct
            except:
                # The exact hour is the present one, which is already the one in timeTarget
                # The text of the alert is given by the following words
                return timeTarget, ' '.join(inputSplit[2:])
         
        # Except: try to parse the 2nd element as an exact hour:minute
        except:
            try:
                # Split the second object as hour:minute
                hour, minute = inputSplit[1].split(':')
                # Modify the hour and minute of the datetime.datetime object
                timeTarget = timeTarget.replace(hour=int(hour), minute=int(minute))
                # If the target is before the current hour, add one day
                print(timeTarget)
                if (timeTarget - datetime.datetime.now()).total_seconds() < 0:
                    timeTarget += datetime.timedelta(days=1)

                print(timeTarget)
                # The text of the alert is given by the words following this
                return timeTarget, ' '.join(inputSplit[2:])
            except:
                # If everything else fails, simply return
                return
    

# def writeAlert(timeString, textAlert, fileAlerts):
#     '''Write a given alert into the file.'''
#     # Convert the timeString to a datetime.timedelta object
#     timeDelta = parseTimeString(timeString)
    
#     # Check if timeDelta is positive. Otherwise return an error.
#     try:
#         if timeDelta.total_seconds() > 0:
#             # Compute the moment when the alarm should go off.
#             timeTarget = datetime.datetime.now() + timeDelta
#             # Write the alert to the file.
#             with open(fileAlerts, 'a') as f:
#                 f.write('{},{}\n'.(timeTarget.isoformat(), textAlert))
#         else:
#             raise WrongTimeInterval
#     except:
#         raise WrongTimeInterval

def writeAlert(inputStringSplitted, fileAlerts):
    '''Write a given alert into the file.'''
    
    try:
        # Convert the inputString to a datetime.datetime object and the text of the message
        timeTarget, textAlert = parseInputAlert(inputStringSplitted)
        # Check if timeTarget is in the future. Otherwise return an error.
        if (timeTarget - datetime.datetime.now()).total_seconds() > 0:
            # Write the alert to the file.
            with open(fileAlerts, 'a') as f:
                f.write('{},{}\n'.format(timeTarget.isoformat(), textAlert))
            return timeTarget
        else:
            raise WrongTimeFormat
    except:
        raise WrongTimeFormat
    

def readAlerts(fileAlerts):
    '''Return the time for the next backup, and a list with all the alerts in the file.
    Each element of the list consists of the datetime object with the moment when
    the alert should go off, and the text of the alert.'''
    
    alerts = []
    
    with open(fileAlerts, 'r') as f:
        # Read the time for the next backup from the first line of the file
        try:
            time_backup_str = f.readline().strip().split(' ')[1]
            time_next_backup = datetime.datetime.fromisoformat(time_backup_str)
        except:
            raise NoTimeBackup
        # Read the programmed alerts from the rest of the file
        for line in f:
            # update.message.reply_text(str(line))
            thisline = line.split(',')
            alerts.append([datetime.datetime.fromisoformat(thisline[0]), 
                           thisline[1].strip()])
    return time_next_backup, alerts




def dropboxConnect():
    '''Handle the connection to Dropbox.'''
    
    # Read the access token
    DROPBOX_TOKEN = ''
    with open("dropbox_token", "r") as f:
        # Get the token from the 5th line
        for i in range(4):
            f.readline()
        DROPBOX_TOKEN = f.readline().strip()

    # Check for an access token
    if (len(DROPBOX_TOKEN) == 0):
        return "DROPBOX ERROR: Looks like you didn't add your access token."

    # Create an instance of a Dropbox class, which can make requests to the API.
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError:
        return "DROPBOX ERROR: Invalid access token."
    
    return dbx
    

def dropboxUpload(dbx, local_file, remote_file):
    '''Upload the contents of local_file to Dropbox.'''
    with open(local_file, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        # print("Uploading " + local_file + " to Dropbox as " + remote_file + "...")
        try:
            dbx.files_upload(f.read(), remote_file, mode=dropbox.files.WriteMode('overwrite'))
        # Check if there are errors in the interaction with the API.
        except dropbox.exceptions.ApiError as err:
            # This checks for the specific error where a user doesn't have enough 
            # Dropbox space quota to upload this file.
            if (err.error.is_path() and err.error.get_path().error.is_insufficient_space()):
                print("ERROR: Cannot upload to Dropbox; insufficient space.")
                # Stop the execution
            elif err.user_message_text:
                print(err.user_message_text)
                # sys.exit()
            else:
                print(err)
                # sys.exit()
                
                
def dropboxDownload(dbx, remote_file):
    '''Returns the binary data in the remote file, and its modification time as a 
    datetime.datetime object.'''
    try:
        md, res = dbx.files_download(remote_file)
        
    # except dropbox.exceptions.HttpError as err:
    #     print('HTTP error: ', err)
    #     return None, None
    except:
        print('Unable to download the remote file.')
        return None
    
    data = res.content
    # print(len(data), 'bytes; md:', md)
    # print(md)
    return data.decode('ascii')

def compareBackupDropbox(updater, chat_id, alerts, time_backup, backupHoursInterval, 
                    fileAlerts, fileAlertsSent):
    '''Download the backup file from dropbox, and update the file with the alerts with
    those that are not in it, and have not been sent either.
    '''
    # Dropbox file to use as backup
    file_alerts_dropbox = '/AlertBot/single_alerts_backup.txt' # Keep the forward slash before destination filename
    
    # updater.dispatcher.bot.send_message(chat_id=chat_id, text='Starting backup process...')
    
    try:
        # Connect to Dropbox
        dbx = dropboxConnect()
        
        # If the object returned above is an error message
        if type(dbx) == str:
            # Send the error as a Telegram message
            # updater.message.reply_text(dbx, parse_mode=parsemode)
            updater.dispatcher.bot.send_message(chat_id=chat_id, text=dbx)
            # Return the original values of the variables
            return time_backup, alerts
        
        # Download the file from Dropbox and read the alerts
        backup_alerts_str = dropboxDownload(dbx, file_alerts_dropbox)
        # Do the following if the alerts were successfuly downloaded
        if backup_alerts_str:
            # Convert this to a list of alerts
            alerts_in_backup = []
            # Recall that the first line is the moment for the next backup
            for line in backup_alerts_str.strip().split('\n')[1:]:
                line = line.split(',')
                alerts_in_backup.append([datetime.datetime.fromisoformat(line[0]), 
                               line[1].strip()])
            # Read the sent alerts from the file
            alerts_sent = []
            with open(fileAlertsSent, 'r') as f:
                for line in f:
                    line = line.split(',')
                    alerts_sent.append([datetime.datetime.fromisoformat(line[0]), 
                               line[1].strip()])
                
            # Append those in the backup to the list of alerts
            # Before appending each of these, check that they are not in the list
            # of alerts, and in the list of sent alerts
            for alert_to_copy in [alert for alert in alerts_in_backup if alert not in alerts
                                  and alert not in alerts_sent]:
                alerts.append(alert_to_copy)
            
    except:
        # Do nothing
        return time_backup, alerts

    # Update the time for the next backup
    time_backup = datetime.datetime.now() + datetime.timedelta(hours=backupHoursInterval)
    # Save the alerts to the local file
    updateAlerts(time_backup, alerts, fileAlerts)
    # Upload the file to Dropbox
    dropboxUpload(dbx, fileAlerts, file_alerts_dropbox)
    # Empty the local file with the sent alerts
    with open(fileAlertsSent, 'w') as f:
        pass
    
    updater.dispatcher.bot.send_message(chat_id=chat_id, text='Backup done')
    
    return time_backup, alerts
        
        

def checkAlerts(alerts, updater, chat_id, parsemode, time_backup, backupHoursInterval,
                fileAlerts, fileAlertsSent):
    '''Send a message if a given alert is set to go off in the current minute.
    Alerts is a list with the time and the text of each alert.'''
    
    # # Check if the time for the backup is in the past.
    # if (datetime.datetime.now() - time_backup).total_seconds() > 0:
    #     # Do the backup (download, compare and upload)
    #     time_backup, alerts = compareBackupDropbox(updater, chat_id, alerts, time_backup, backupHoursInterval, 
    #                                           fileAlerts, fileAlertsSent)
    
    # List to store the alerts that will be removed
    alerts_to_remove = []
    
    for alert in alerts:
        # Check if the alert is set to go off in this minute.
        if (datetime.datetime.now() - alert[0]).total_seconds() > 0:
            # Send a telegram message with the text of the alert.
            updater.dispatcher.bot.send_message(chat_id = chat_id, text = alert[1], 
                                                parse_mode = parsemode)
            # Add this to the alerts that will be removed
            alerts_to_remove.append(alert)
    # Remove the alerts that need to
    new_alerts = alerts.copy()
    for a in alerts_to_remove:
        new_alerts.remove(a)
        
    return new_alerts, alerts_to_remove


def updateAlerts(time_next_backup, alerts, fileAlerts):
    '''Update the file of alerts with the current alerts.
    This will be called only if the list of alerts has changed, either because
    some of them has gone off or has been edited or deleted.'''
    with open(fileAlerts, 'w') as f:
        # Write the time for the next backup
        f.write('next_backup {}\n'.format(time_next_backup.isoformat()))
        # Write the alerts
        for alert in alerts:
                f.write('{},{}\n'.format(alert[0].isoformat(), alert[1]))
    return


def updateSentAlerts(sent_alerts, fileAlertsSent):
    '''Update the file of alerts that have been set with the current alerts.
    This will be called only if there are some new alerts sent.'''
    with open(fileAlertsSent, 'a') as f:
        # Write the alerts
        for alert in sent_alerts:
                f.write('{},{}\n'.format(alert[0].isoformat(), alert[1]))
    return


def sendAlerts(updater, chat_id, fileAlerts, fileAlertsSent, backupHoursInterval, parsemode):
    '''This function will be executed in a background thread every ALERTS_TIME_INTERVAL
    seconds (default 60). It sends to the user the alerts that are due in that minute.'''
    
    global time_next_backup_global
    
    # print('sending alerts')
    
    # Read the alerts and the moment for the next backup
    time_backup, alerts = readAlerts(fileAlerts)
    
    # Check the alerts, and send the messages for those that go off
    # This function also returns the moment of the next backup, which is updated
    # when the backup is done. Otherwise it is not changed.
    new_alerts, sent_alerts = checkAlerts(alerts, updater, chat_id, 
                                                           parsemode, time_backup, 
                                                           backupHoursInterval,
                                                           fileAlerts, fileAlertsSent)
    
    # If the alerts changed, update the files
    if alerts != new_alerts:
        # Update the file with the scheduled alerts
        updateAlerts(time_backup, new_alerts, fileAlerts)
        # Append the sent alerts to their file
        updateSentAlerts(sent_alerts, fileAlertsSent)
        
    # Check if the time for the backup is in the past.
    if (datetime.datetime.now() - time_backup).total_seconds() > 0:
        # Do the backup (download, compare and upload)
        time_backup, alerts = compareBackupDropbox(updater, chat_id, new_alerts, time_backup, backupHoursInterval, 
                                              fileAlerts, fileAlertsSent)
        # Update the global variable with the time of the next backup
        time_next_backup_global = time_backup
        
    # # Check if a backup has just been done.
    # if time_backup != new_time_backup:
    #     # Update the global variable with the time of the next backup
    #     time_next_backup_global = new_time_backup
    #     # Empty the file with the alerts that have been sent.
    #     with open(fileAlertsSent, 'w') as f:
    #         pass


            

if __name__ == '__main__':
    
    pass
                
    # alerts = readAlerts(FILE_ALERTS)
    # print(alerts)
    