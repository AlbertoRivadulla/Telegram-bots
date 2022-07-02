#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 21:40:32 2020

@author: alberto
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




################# Functions of the bot ######################

def read_ids(file_ids):
    '''Read the pairs of name:id in the given file, and return them as a dictionary.'''
    # Create a dictionary
    dictionary = {}
    # Read everything from the file
    with open(file_ids, 'r') as f:
        for line in f:
            # Split this line
            thisline = line.strip().split(';')
            # Add them as pairs name:id to the dictionary
            dictionary[thisline[0]] = thisline[1]
    
    return dictionary


def next_weekday(day_now, target_weekday, target_hour):
    '''Returns the datetime.datetime object for the next given weekday target_weekday counting from the
    reference day_now given.'''
    # Compute the days ahead
    days_ahead = (target_weekday - day_now.isoweekday())%7
    if days_ahead == 0:
        days_ahead = 7
    # Compute the target day
    target_day = day_now + datetime.timedelta(days=days_ahead)
    # Set the given hour of the target day, and return it
    return target_day.replace(hour=target_hour, minute=0)


if __name__ == '__main__':
    
    pass
                
    # alerts = readAlerts(FILE_ALERTS)
    # print(alerts)
    
