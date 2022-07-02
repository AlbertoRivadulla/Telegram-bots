#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 18:42:05 2020

@author: alberto

List of commands (for BotFather)

localip - Local IP address
mountdrives - Mount all drives
ummountpen - Ummount the Sandisk pendrive
temp - Current temperature
plottemp - Plot the temperature in an interval of time
stop - Stop the bot
shutdown - Shutdown the Pi

"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from telegram import KeyboardButton, ReplyKeyboardMarkup, ParseMode
import logging

import threading # Needed for the \stop command, and to run processes in background
from queue import Queue
from subprocess import Popen, PIPE, STDOUT # Needed for the \battery command
from socket import socket, AF_INET, SOCK_DGRAM # Needed for the \localIP command

from telegram.error import NetworkError

from io import BytesIO
import matplotlib.pyplot as plt

# Read the tokens
TOKEN = ''
CHAT_ID = ''
with open("token", "r") as f:
    # The information in the first two lines is not important
    for i in range(2):
        f.readline()
    # The third line is the token
    TOKEN = f.readline().strip()
    # The fourth line is the chat id
    CHAT_ID = f.readline().strip()

updater = Updater(token=TOKEN, use_context=True)

#Set up the logging module, so you will know when things don't work as expected
#This is used to print in the terminal the errors that are not caused by the 
#Telegram API (eg, Python errors)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def error_callback(update, context):
    try:
        raise context.error
    # except Unauthorized:
    #     # remove update.message.chat_id from conversation list
    # except BadRequest:
    #     # handle malformed requests - read more below!
    # except TimedOut:
    #     # handle slow connection problems
    except NetworkError:
        # Stop the bot if the internet connection fails
        print("connection error")
        # threading.Thread(target = shutdown).start()
        pass
    # except ChatMigrated as e:
    #     # the chat_id of a group has changed, use e.new_chat_id instead
    # except TelegramError:
    #     # handle all other telegram related errors
        
updater.dispatcher.add_error_handler(error_callback)



##################   COMMANDS   ##########################    

def startFunction(update, context):
    '''Function that replies with a text, simply to let the user know that the bot
    is working as an AlertBot.
    This will be called with the /start command.'''
    update.message.reply_text(text = 'Hi! This bot allows you to control your Raspberry Pi system.',
                              parse_mode = ParseMode.MARKDOWN)
    
def helpFunction(update, context):
    '''Function that replies with a text, simply to let the user know the available
    commeands.
    This will be called with the /help command.'''
    message = 'The available commands are:\n' + \
        '\t\t\t\t/localIP: get the local IP address of the Pi.\n' + \
        '\t\t\t\t/ummountPen: ummount the Sandisk pendrive.\n' + \
        '\t\t\t\t/mountDrives: mount all drives, as defined in /etc/fstab.\n' + \
        '\t\t\t\t/temp: get the temperature of the Pi.\n' + \
        '\t\t\t\t/plotTemp <seconds>: plot the temperature of the Pi during a given amount of seconds.\n' + \
        '\t\t\t\t/stop: shutdown the bot.\n' + \
        '\t\t\t\t/shutdown: shutdown the Pi.\n'   
        
    update.message.reply_text(text = message, parse_mode = ParseMode.MARKDOWN)



#######################

# Function to stop the execution of the bot.
def shutdown():
    print("Stopping bot...")
    updater.stop()
    updater.is_idle = False
    
# The following function is called with the /stop command
# It executes shutdown() in a new thread, stopping the execution of the bot
def stopFunction(update, context):
    threading.Thread(target = shutdown).start()
    update.message.reply_text(text = 'Stopping bot...')
    
    
    
####################### 

def shutdownFunction(update, context):
    '''Shutdown the Raspberry.'''
    update.message.reply_text(text = 'Shutting down the system...')
    Popen('sudo shutdown -h now'.split(), stdout=PIPE)
    
    
    
#######################

def mountDrivesFunction(update, context):
    '''Mount all drives as defined in /etc/fstab.'''
    # Ummount the pendrive    
    process = Popen(r'sudo mount -a', stdout=PIPE, shell = True)
    process.communicate()[0]
    # Get the returncode for this process
    rc = process.returncode    
    # If the returncode is zero, the process was run successfully
    if rc == 0:
        update.message.reply_text(text = 'Drives mounted!')
    else:
        update.message.reply_text('Unable to mount the drives.')
        

def ummountPenFunction(update, context):
    '''Umount the Sandisk pendrive.'''
    
    # The UUID of the pendrive
    UUID = "D228-3576"
    
    # Check if the pendrive is mounted
    check_mountpoint_process= Popen(r'lsblk -o UUID,MOUNTPOINT | grep {}'.format(UUID), 
                                    stdout=PIPE, stderr=STDOUT, shell = True)
    # Run the process and get the stdout of the command.
    # The standard error would be the second element given.
    check_mountpoint_stdout = check_mountpoint_process.communicate()[0].decode('ascii').strip()
    # Check if this is mounted.
    if check_mountpoint_stdout.endswith(r'/media/Sandisk-drive'):
        # Ummount the pendrive    
        process = Popen(r'sudo umount /media/Sandisk-drive'.split(), stdout=PIPE)
        process.communicate()[0]
        # Get the returncode for this process
        rc = process.returncode    
        # If the returncode is zero, the process was run successfully
        if rc == 0:
            update.message.reply_text(text = 'Pendrive ummounted!')
        else:
            update.message.reply_text('Unable to ummount the pendrive.')
    else:
        update.message.reply_text('The pendrive was not mounted.')

########################

def temperatureFunction(update, context):
    '''Function that replies with the temperature of the system.'''
    try:
        # Get the temperature of the system.
        temperature = Popen('vcgencmd measure_temp'.split(), 
                                      stdout=PIPE).communicate()[0].decode('ascii')
        
        # Format the output
        temperature = float(temperature.replace("temp=", "").replace("\'C", ""))
        
        # Add an emoji at the end of the message depending on the temperature range.
        if temperature >= 54:
            emoji = "🥵"
        elif temperature < 45:
            emoji = "🥶"
        else:
            emoji = "👍"
        update.message.reply_text(text = "Temperature: {}ºC".format(temperature))
        update.message.reply_text(text = emoji)
    except:
        update.message.reply_text(text = "Unable to obtain the temperature of the system.\n" + \
                                  "Are you sure this is a Raspberry Pi? 🙄")
            

def getTemperatureToPlot(seconds_measure, seconds_average, queue_temp, update):
    '''This will be executed by the function plotTemperatureFunction below, called
    with the command \plotTemp <seconds>.'''
    
    # Create a threading.Timer object, that executes this function recursively
    # every 1 second.
    # Then start the process.
    getTempProcess = threading.Timer(1, getTemperatureToPlot, 
                                     args=(seconds_measure, seconds_average, queue_temp, update))
    getTempProcess.start()
    
    # Unpack everything from the queue
    seconds_elapsed, time_list, temperature_list = queue_temp.get()
        
    # Measure the temperature
    temperature_now = float(Popen('vcgencmd measure_temp'.split(), 
                                stdout=PIPE).communicate()[0].decode('ascii').replace("temp=", "").replace("\'C", ""))
    # temperature_now = seconds_elapsed**2
    # Store the time and temperature in the lists
    time_list.append(seconds_elapsed)
    temperature_list.append(temperature_now)
    # Increase the amount of seconds
    seconds_elapsed += 1
    
    # Put everything again in the queue
    queue_temp.put((seconds_elapsed, time_list, temperature_list))    
    
    if seconds_elapsed >= seconds_measure:
        # Stop the process and delete the queue.
        getTempProcess.cancel()
        del queue_temp
        
        time_list_avg = time_list[:-(seconds_average - 1)]
        temperature_list_avg = [0] * (len(temperature_list) - (seconds_average - 1))
        for i in range(len(temperature_list_avg)):
            temperature_list_avg[i] = sum([temperature_list[j] for j in [i+k for k in range(seconds_average)]
                         ]) / seconds_average
            
        # Create the plot
        fig = plt.figure()
        plt.plot(time_list_avg, temperature_list_avg)
        plt.title('Moving average: {} seconds'.format(seconds_average))
        plt.xlabel('Time [s]')
        plt.ylabel('Temperature [ºC]')
        # Store the plot in a buffer in memory
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        # Send the plot as an image in telegram
        buffer.seek(0)
        update.message.reply_photo(photo = buffer)
        
        # Close the buffer in memory
        buffer.close()
        # Delete the created figure from the memory
        del fig
        
        return
    
    
def plotTemperatureFunction(update, context):
    '''Function to plot the temperature of the Raspberry over time.'''
    # Read the text in the message
    input_text = update.message.text.split(' ')
    
    # The second argument will be the amount of seconds
    try:
        # Get the amount of seconds from the argument given in the message.
        second_argument = input_text[1].strip()
        # Check if the interval is given in seconds or minutes.
        if second_argument[-1] == 's':
            # Get the seconds directly.
            seconds_measure = int(second_argument[:-1])
        elif second_argument[-1] == 'm':
            # Convert to seconds.
            seconds_measure = 60 * int(second_argument[:-1])
        else:
            update.message.reply_text('*Wrong syntax!*\nYou should write:\n' + \
                                      '/plottemp <time><s or m>,\nfor seconds or minutes' + \
                                      '\nor\n/plottemp <time><s or m> <seconds to average>,' + \
                                      '\nfor seconds or minutes.',
                                  parse_mode = ParseMode.MARKDOWN)
            return
    
        # Check if there is a second argument with the amount of seconds on which
        # to run the moving average.
        if len(input_text) == 3:
            seconds_average = int(input_text[2].strip())
        else:
            # Default interval
            seconds_average = 1
        
        update.message.reply_text('Gathering measurements...', parse_mode = ParseMode.MARKDOWN)
        
        # List with the number of seconds elapsed in each point of the plot.
        time_list = []
        # Time elapsed since the beginning.
        seconds_elapsed = 0
        # List to store the measured temperatures.
        temperature_list = []
        # Put all of the variables that will be updated in a queue, so they can be
        # modified by the thread
        queue_temp = Queue()
        queue_temp.put((seconds_elapsed, time_list, temperature_list))
        
        # Get the temperatures in a separate thread
        getTemperatureToPlot(seconds_measure, seconds_average, queue_temp, update)
        
    except:
        update.message.reply_text('*Wrong syntax!*\nYou should write:\n' + \
                                      '/plottemp <time><s or m>,\nfor seconds or minutes' + \
                                      '\nor\n/plottemp <time><s or m> <seconds to average>,' + \
                                      '\nfor seconds or minutes.',
                                  parse_mode = ParseMode.MARKDOWN)


#######################

def getLocalIP():    
    # Open a connection with '8.8.8.8' in port 80 (Google's public DNS)
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    # Get the IP address from there.
    localIPaddress = s.getsockname()[0]
    s.close()
    
    return localIPaddress


def localIPFunction(update, context):
    '''Function that replies with the local IP address of the system.'''
        # Show the status of the bot as typing...
    context.bot.send_chat_action(chat_id = update.effective_chat.id, 
                                 action = ChatAction.TYPING)
    # Send the results in a well formatted message.
    update.message.reply_text(text = 'Local IP address: {}'.format(getLocalIP()))



#####################   TEXT RECOGNITION   ################

def unknownFunction(update, context):
    '''This will be sent when the bot receives a message with an unknown command.'''
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Sorry, I didn't understand that command.")



##############################################################

# Add the handlers for the commands defined above
updater.dispatcher.add_handler(CommandHandler('start', startFunction))
updater.dispatcher.add_handler(CommandHandler('help', helpFunction))
updater.dispatcher.add_handler(CommandHandler('stop', stopFunction))
updater.dispatcher.add_handler(CommandHandler('shutdown', shutdownFunction))
updater.dispatcher.add_handler(CommandHandler('localip', localIPFunction))
updater.dispatcher.add_handler(CommandHandler('temp', temperatureFunction))
updater.dispatcher.add_handler(CommandHandler('plottemp', plotTemperatureFunction))
updater.dispatcher.add_handler(CommandHandler('ummountpen', ummountPenFunction))
updater.dispatcher.add_handler(CommandHandler('mountdrives', mountDrivesFunction))
# # Add the handler for clicks in the buttons of inline keyboards
# updater.dispatcher.add_handler(CallbackQueryHandler(inlineButtonPress))
# MessageHandler with a command filter to reply to all commands that were not 
# recognized by the previous handlers.
updater.dispatcher.add_handler(MessageHandler(Filters.command, unknownFunction))



# Notify the user that the bot is working
updater.dispatcher.bot.send_message(chat_id = CHAT_ID, text = "I'm working! 🤙\nMy local IP address is {}".format(getLocalIP()))

# Start the bot
updater.start_polling()

# Keep the bot executing until pressing Ctrl+C
updater.idle()



# Stop the bot
# updater.stop()
