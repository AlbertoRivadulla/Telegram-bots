#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 21:40:32 2020

@author: alberto

"""

# Import my other Python script
from alerts import *

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ChatAction
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import NetworkError

import logging

import threading # Needed for the \stop command
# from subprocess import Popen, PIPE # Needed for the \battery command
# from socket import socket, AF_INET, SOCK_DGRAM # Needed for the \localIP command

# Needed to read the callback_query data as Python code
import ast

# import time
# from telegram.ext.dispatcher import run_async

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

# Files that store the alerts
FILE_ALERTS = 'single_alerts.txt'
FILE_PERIODIC = 'periodic_alerts.txt'
# File to store the alerts that have already been sent
FILE_ALERTS_SENT = 'single_alerts_sent.txt'

# Time interval for checking and sending alerts (in seconds)
ALERTS_TIME_INTERVAL = 60
# Time interval for uploading backups to Dropbox
BACKUPS_HOURS_INTERVAL = 8

# Global variable to store the alerts in memory.
alerts = []

# Global variable with the time for the next backup.
time_next_backup_global = datetime.datetime.now()

# Format to print the datetime objects in the Telegram messages
FORMAT_DATETIME = '%d/%m/%y %H:%M'

# Boolean variable that will be set to True when an alert is going to be edited in the chat
BOOL_EDIT_ALERT = False
# Variable to store the index of the alert to edit
INDEX_EDIT_ALERT = 0
# Variable to store the ID of the message that will be modified after editing a message
MESSAGE_ID_EDIT = 0



# The Updater class continuously fetches new updates from telegram and passes 
# them on to the Dispatcher class
updater = Updater(token = TOKEN, use_context=True)

# # The Dispatcher is created automatically with the Updater.
# # For quicker access, we can introduce it locally
# dispatcher = updater.dispatcher

# Set up the logging module, so you will know when things don't work as expected
# This is used to print in the terminal the errors that are not caused by the 
# Telegram API (eg, Python errors)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def error_callback(update, context):
    try:
        raise context.error
    except NetworkError:
        # Stop the bot if the internet connection fails
        print("Connection error")
        pass
        
updater.dispatcher.add_error_handler(error_callback)



##################   COMMANDS   ##########################    

def startFunction(update, context):
    '''Function that replies with a text, simply to let the user know that the bot
    is working as an AlertBot.
    This will be called with the /start command.'''
    # context.bot.send_message(chat_id=update.effective_chat.id, 
    #                          text="Hi! This is working as an AlertBot now.")
    update.message.reply_text(text = 'Hi! This is working as an *AlertBot*.',
                              parse_mode = ParseMode.MARKDOWN)
    
def helpFunction(update, context):
    '''Function that replies with a text, simply to let the user know the available
    commeands.
    This will be called with the /help command.'''
    message = 'The available commands are:\n' + \
        '\t\t\t\t/alert: set an alert.\n' + \
        '\t\t\t\t/alerts: see a list of the programmed alerts (in the future it will be possible to modify them).'
    update.message.reply_text(text = message, parse_mode = ParseMode.MARKDOWN)


#######################

# Function to stop the execution of the bot.
def shutdown():
    print("Stopping bot...")
    updater.stop()
    updater.is_idle = False
    # Stop the process that sends the alerts periodically
    sendAlertsProcess.stop()
    
# The following function is called with the /stop command
# It executes shutdown() in a new thread, stopping the execution of the bot
def stopFunction(update, context):
    threading.Thread(target = shutdown).start()
    
    update.message.reply_text(text = 'Stopping bot...')
    
    
######################
    
def setAlert(update, context):
    '''Set an alert after an amount of time given in the message. 
    This is called as
        /alert <time interval> <text>
    '''
    # Read the text in the message
    input_text = update.message.text.strip().split(' ')
    
    # Check if the syntax is correct. Otherwise, reply to the user
    if len(input_text) <= 2:
        update.message.reply_text(text = 
                                  '*Wrong syntax!*\nYou should write:\n\t\t/alert <time> <text>\n' + \
                                   '*Available formats for the time:*\n' + \
                                   '\t\t1y2mo3w4d5h6m\n' + \
                                   '\t\t1y2mo3d hh:mm\n' + \
                                   '\t\tYY/MM/DD hh:mm or MM/DD hh:mm\n' + \
                                   '\t\t12:30 (today)\n',
                                  parse_mode = ParseMode.MARKDOWN)
    else:
        # # Separate the message into the time string and the text of the alert
        # time_string = input_text[1]
        # text = ' '.join(input_text[2:])
        # # Save the alert in the file
        try:
            # Save the alert in the file, and get the time when it should go off
            timeTarget = writeAlert(input_text, FILE_ALERTS)
            # Notify that the alert has been set
            update.message.reply_text('Alert set for {}.'.format(timeTarget.strftime(FORMAT_DATETIME)))
        except WrongTimeFormat:
            update.message.reply_text('The time interval written is not correct.\nIt should be written as\n\t\t1y2mo3w4d5h6m')
        

############################

def keyboardAlertList(alerts):
    '''Create the keyboard with the list of alerts.'''
    return InlineKeyboardMarkup([[InlineKeyboardButton(alerts[i][0].strftime(FORMAT_DATETIME) + 
                                                       ' - ' + alerts[i][1], 
                                      callback_data = "{'type':'alertSelection', 'index':" + str(i) + "}")]
                for i in range(len(alerts))] + \
                [[InlineKeyboardButton('Cancel', callback_data="{'type':'alertAction', 'action':'cancel'}")]])

def checkAlertList(update, context):
    '''Send a message with all the alerts that are set for the future.'''
    global alerts
    # Read the alerts
    _, alerts = readAlerts(FILE_ALERTS)
    
    if len(alerts) == 0:
        update.message.reply_text('There are no alerts programmed.')
        return

    # Create an inline keyboard whose buttons correspond to each of the alerts.
    update.message.reply_text('Programmed alerts:', 
                              reply_markup = keyboardAlertList(alerts)) 
    
def inlineButtonPress(update, context):
    '''What to do when a button in an inline keyboard is pressed.'''
    # Get the callback query that has been sent
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    
    # Read the data in the query as Python code (it is a dictionary, written as a string)
    data = ast.literal_eval(query.data)
    
    # The variable alerts is the global one
    global alerts
    global BOOL_EDIT_ALERT
    global INDEX_EDIT_ALERT
    global MESSAGE_ID_EDIT
    
    # Check if the user pressed a button that is an alert (the keyboard created by checkAlertList)
    if data['type'] == 'alertSelection':
        # Then, data has an item with the key ID that is the index of the alert in the list

        # Display the selected alert
        message = 'Selected alert:\n\n*' + alerts[int(data['index'])][0].strftime(FORMAT_DATETIME) + ' - ' + \
                    alerts[int(data['index'])][1] + '*'

        # Display a new keyboard that allows to edit, duplicate or delete the alert        
        keyboard = [[InlineKeyboardButton('Edit', callback_data="{'type':'alertAction', 'action':'edit', 'index':" + str(data['index']) + "}"), 
                  InlineKeyboardButton('Duplicate', callback_data="{'type':'alertAction', 'action':'duplicate', 'index':" + str(data['index']) + "}"),
                  InlineKeyboardButton('Delete', callback_data="{'type':'alertAction', 'action':'delete', 'index':" + str(data['index']) + "}")],
                  [InlineKeyboardButton('Back', callback_data="{'type':'alertAction', 'action':'back'}"),
                  InlineKeyboardButton('Cancel', callback_data="{'type':'alertAction', 'action':'cancel'}")]]
        
        query.edit_message_text(text = message, parse_mode = ParseMode.MARKDOWN,
                                reply_markup = InlineKeyboardMarkup(keyboard))

    # Check if the user pressed a button to perform an action on an alert.
    if data['type'] == 'alertAction':
        
        # Check the all the possible actions
        if data['action'] == 'edit':
            # Set to true the boolean variable, so the updater listens for the new
            # text of the alert
            BOOL_EDIT_ALERT = True
            # Store the index of the alert in the global variable
            INDEX_EDIT_ALERT = data['index']
            # Store the ID of the previous message, so it can be modified later
            MESSAGE_ID_EDIT = query.message.message_id
            
            # Prompt the user to write the new text for the alert.
            keyboardEdit = [[InlineKeyboardButton('Cancel', callback_data="{'type':'alertAction', 'action':'cancel'}")]]
            messageEdit = 'Selected alert:\n\n*' + alerts[int(data['index'])][0].strftime(FORMAT_DATETIME) + ' - ' + \
                    alerts[int(data['index'])][1] + '*\n\nWrite the new time or text for the alert.'
            query.edit_message_text(messageEdit, parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboardEdit))
        
        elif data['action'] == 'duplicate':
            query.edit_message_text('The function to duplicate alerts is not implemented yet.')
        
        elif data['action'] == 'delete':
            # Add this alert to the file with the sent alerts, so it is ignored when
            # downloading the backup.
            # Notice that the alerts have to be passed as a list
            updateSentAlerts((alerts[int(data['index'])],), FILE_ALERTS_SENT)
            
            # Remove this alert from the list
            alerts.remove(alerts[int(data['index'])])
            # Write the edited list of alerts to the file
            updateAlerts(time_next_backup_global, alerts, FILE_ALERTS)
            
            # Show again the keyboard with the alerts
            query.edit_message_text('Programmed alerts, edited:', 
                              reply_markup = keyboardAlertList(alerts))
            
        elif data['action'] == 'back':
            # Show again the keyboard with the list of alerts
            query.edit_message_text('Programmed alerts:', 
                                      reply_markup = keyboardAlertList(alerts)) 
            
        elif data['action'] == 'cancel':
            # Delete this message
            query.bot.delete_message(query.message.chat_id, query.message.message_id)
            # Set the boolean variable to edit to false
            BOOL_EDIT_ALERT = False
        


#####################   TEXT RECOGNITION   ######################


def unknownFunction(update, context):
    '''This will be sent when the bot receives a message with an unknown command.'''
    context.bot.send_message(chat_id=update.effective_chat.id, 
                              text="Sorry, I didn't understand that command.")
    
    
def editAlertFunction(update, context):
    '''Modify the text of an alert.'''
    # Get the global variables
    global BOOL_EDIT_ALERT
    global INDEX_EDIT_ALERT
    global MESSAGE_ID_EDIT
    global alerts
    
    # Check if there is an alert to edit (set by clicking the 'Edit' button in a keyboard)
    if BOOL_EDIT_ALERT:
        
        # Add the old alert to the file of sent alerts, so it is not recovered when
        # consulting the backup in Dropbox
        updateSentAlerts((alerts[INDEX_EDIT_ALERT],), FILE_ALERTS_SENT)
        
        # Try to parse the text written for the alert as if it were an alert
        parsed_text = parseInputAlert([' '] + update.message.text.strip().split(' '))
        
        # If the it was parsed as a timestring successfully
        if parsed_text != None:
            # Update the time of the alert
            alerts[INDEX_EDIT_ALERT][0] = parsed_text[0]
            # If it had a text also, update the text
            if parsed_text[1] != '':
                alerts[INDEX_EDIT_ALERT][1] = parsed_text[1]
        # Otherwise, the user only wrote a text for the alert
        else:
            alerts[INDEX_EDIT_ALERT][1] = update.message.text
        
        # Update the file with the alerts
        updateAlerts(time_next_backup_global, alerts, FILE_ALERTS)
        
        # Set the variable to False, to stop listening for edits
        BOOL_EDIT_ALERT = False
        
        # Notify the user that the alert has been edited.
        context.bot.edit_message_text(text='Alert updated to:\n\n*' + alerts[INDEX_EDIT_ALERT][0].strftime(FORMAT_DATETIME) + \
                                      ' - ' + alerts[INDEX_EDIT_ALERT][1] + '*',
                                      parse_mode=ParseMode.MARKDOWN,
                                      chat_id=CHAT_ID, message_id=MESSAGE_ID_EDIT)
        


##############################################################

# Add the handlers for the commands defined above
updater.dispatcher.add_handler(CommandHandler('start', startFunction))
updater.dispatcher.add_handler(CommandHandler('stop', stopFunction))
updater.dispatcher.add_handler(CommandHandler('help', helpFunction))
updater.dispatcher.add_handler(CommandHandler('alert', setAlert))
updater.dispatcher.add_handler(CommandHandler('alerts', checkAlertList))
# Add the handler for clicks in the buttons of inline keyboards
updater.dispatcher.add_handler(CallbackQueryHandler(inlineButtonPress))

# MessageHandler with a command filter to reply to all commands that were not 
# recognized by the previous handlers.
updater.dispatcher.add_handler(MessageHandler(Filters.command, unknownFunction))

# Add the handler for reading text, which will edit the alerts when required
updater.dispatcher.add_handler(MessageHandler(Filters.text, editAlertFunction))




# Notify the user that the bot is working
updater.dispatcher.bot.send_message(chat_id = CHAT_ID, text = "This is working!")


# Try to read the time for the next backup and the alerts from the file
# If not possible, write the time for the next backup, which is in an hour.
# This needs to be done before starting the process that reads and sends the alerts
# periodically.
try:
    # Read the time for the next backup and the alerts from FILE_ALERTS
    time_next_backup_global, alerts = readAlerts(FILE_ALERTS)
    
except NoTimeBackup:
    # Write as the first line in the file the time for the next backup.
    time_next_backup_global = datetime.datetime.now()
    
    # Read and store the contents of the file
    with open(FILE_ALERTS, 'r') as f:
        file_contents = f.read()
        
    # Write to the file the time for the next backup, and then the file contents.
    with open(FILE_ALERTS, 'w') as f:
        f.write('next_backup {}\n'.format(time_next_backup_global.isoformat()))
        f.write(file_contents)
        
    # Notify the user that there was no backup time programmed.
    updater.dispatcher.bot.send_message(chat_id = CHAT_ID, text = 'There was no backup programmed. Doing one now.')
        
    # Delete the variable that stored the file contents
    del file_contents
    

# Start the process that looks for alerts that are due and sends the messages
# to the user
# This is stopped with the /stop command, by the line sendAlertsProcess.stop()
# in the function shutdown()
# I also add sendAlertsProcess.stop() at the end of the code, so this is stopped
# if I press Ctrl+C
sendAlertsProcess = myTimer(sendAlerts, wait_seconds = ALERTS_TIME_INTERVAL,
                            args = (updater, CHAT_ID, FILE_ALERTS, FILE_ALERTS_SENT, 
                                    BACKUPS_HOURS_INTERVAL, ParseMode.MARKDOWN))

#sendAlertsProcess = threading.Timer(ALERTS_TIME_INTERVAL, sendAlerts)
sendAlertsProcess.start()


# Start the bot
updater.start_polling()

# Keep the bot executing until pressing Ctrl+C
updater.idle()

# Stop the process that sends the alerts.
sendAlertsProcess.stop()




# Stop the bot
# updater.stop()
