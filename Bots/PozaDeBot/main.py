#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 21:40:32 2020

@author: alberto


Add functionality to the keyboard with the list of notes.
    Set an alert
    
Add functionality to, instead of deleting, sending the alerts to a list of done alerts
        
Add the functionality to undo the last change (editing a note/description, or deleting it)
        
Add a command /createlist to create a new list.
    The names of the lists must be in a separate file, which is read when the program
    is run, so it can be modified.

Add a command /deletelist to delete a list.

"""

# Import my other Python script
from poza_methods import *

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
#from telegram import ChatAction
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import NetworkError

import logging

import threading # Needed for the \stop command
# from subprocess import Popen, PIPE # Needed for the \battery command
# from socket import socket, AF_INET, SOCK_DGRAM # Needed for the \localIP command

# Needed to read the callback_query data as Python code
import ast

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

# File where the tasks are programed
FILE_TASKS = './Files/tarefas.txt'
# List of tasks
TASKS = ['baño', 'cociña', 'sala e corredor', 'descansar']
# Time interval for the periodic function, in seconds
ALERTS_TIME_INTERVAL = 3600

# Get the dictionary of IDs from the file
IDs = read_ids('./Files/IDs.txt')




#Prefix of the files to store the lists of notes
#FILE_PREFIX = './Lists/list_{}.txt'
#File to store the alerts that have already been sent
#FILE_DELETED_PREFIX = './Lists/list_deleted_{}.txt'
#File where the programmed alerts will be stored
#FILE_ALERTS = '../AlertBot/single_alerts.txt'

#Format to print the datetime objects in the Telegram messages
#FORMAT_DATETIME = '%d/%m/%y %H:%M'

# # # Time interval for uploading backups to Dropbox
# BACKUPS_HOURS_INTERVAL = 8
# # Global variable with the time for the next backup.
# time_next_backup_global = datetime.datetime.now()

#Global variable to store the alerts in memory.
#NOTES = []

#Boolean variable to be set to true when we want to set an alert, so the updater
#listens for a time string
#BOOL_SET_ALERT = False
#Boolean variables that will be set to True when a note or its description is 
#going to be edited in the chat
#BOOL_EDIT_NOTE = False
#BOOL_EDIT_NOTE_DESCR = False
#Variable to store the index of the note to edit
#INDEX_NOTE = 0
#Variable to store the name of the list in which is the alert that we are editing
#LIST_NOTE = ''
#Variable to store the ID of the message that will be modified after editing a note
#MESSAGE_ID_EDIT = 0



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
    update.message.reply_text(text = 'Ei! Aquí Poza de Bar!',
                              parse_mode = ParseMode.MARKDOWN)
    print(update.message)
    
    
def helpFunction(update, context):
    '''Function that replies with a text, simply to let the user know the available
    commeands.
    This will be called with the /help command.'''
    message = 'De momento isto non ten comandos.'
    update.message.reply_text(text = message, parse_mode = ParseMode.MARKDOWN)


#######################

# Function to stop the execution of the bot.
def shutdown():
    print("Stopping bot...")
    updater.stop()
    updater.is_idle = False
    # # Stop the process that sends the alerts periodically
    # backupsProcess.stop()
    
# The following function is called with the /stop command
# It executes shutdown() in a new thread, stopping the execution of the bot
def stopFunction(update, context):
    threading.Thread(target = shutdown).start()
    
    update.message.reply_text(text = 'Stopping bot...')
    
    
    
    
###################### Handle the lists #####################

def keyboardNotesList(notes, listname):
    '''Create a keyboard with the list of notes given.'''
    return InlineKeyboardMarkup([[InlineKeyboardButton(notes[i][0], 
                                                       callback_data="{'type':'note', 'i':" + \
                                                           str(i) + ", 'list':'" + listname + "'}")]
                                        for i in range(len(notes))] + \
                                       [[InlineKeyboardButton('Cancel', callback_data="{'type':'act', 'act':'cancel'}")]])


def messageNoteText(listname, note):
    '''Get the text to be sent to the Telegram client, showing the note, its list
    and its description, if it exists.'''
    if note[1]:
        return "List *{}*.\n\n*{}*\n{}".format(listname, note[0], note[1])
    else:
        return "List *{}*.\n\n*{}*".format(listname, note[0])
    

def checkNotesList(update, context, listname):
    '''Send a message with all the notes that are in the list, as a keyboard.'''
    global NOTES
    try:
        # Read the notes
        NOTES = readNotes(FILE_PREFIX, listname)
        if len(NOTES) == 0:
            update.message.reply_text('There are no notes in this list.')
            return
        # Send a keyboard with all the notes
        update.message.reply_text('Notes in *' + listname + '* list:', parse_mode=ParseMode.MARKDOWN, 
                                  reply_markup=keyboardNotesList(NOTES, listname))
    
    except FileNotFoundError:
        update.message.reply_text('There are no notes in this list.')

        return
    

def inlineButtonPress(update, context):
    # What to do when a button in an inline keyboard is pressed.
    
    # Get the callback query that has been sent
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    
    # Read the data in the query as Python code (it is a dictionary, written as a string)
    data = ast.literal_eval(query.data)
    
    # The variable alerts is the global one
    global NOTES
    global BOOL_SET_ALERT
    global BOOL_EDIT_NOTE
    global BOOL_EDIT_NOTE_DESCR
    global INDEX_NOTE
    global LIST_NOTE
    global MESSAGE_ID_EDIT
    
    # Check if the user pressed a button that is an alert (the keyboard created by checkAlertList)
    if data['type'] == 'note':
        # Display a new keyboard that allows to edit or delete the alert        
        keyboard = [[InlineKeyboardButton('Edit', callback_data="{'type':'act', 'act':'edit', 'i':" + str(data['i']) + ", 'list':'" + str(data['list']) + "'}"), 
                  InlineKeyboardButton('Delete', callback_data="{'type':'act', 'act':'delete', 'i':" + str(data['i']) + ", 'list':'" + str(data['list']) + "'}"),
                  InlineKeyboardButton('Set alert', callback_data="{'type':'act', 'act':'alert', 'i':" + str(data['i']) + ", 'list':'" + str(data['list']) + "'}")],
                  [InlineKeyboardButton('Back', callback_data="{'type':'act', 'act':'back', 'list':'" + str(data['list']) + "'}"),
                  InlineKeyboardButton('Cancel', callback_data="{'type':'act', 'act':'cancel'}")]]
        
        query.edit_message_text(text=messageNoteText(data['list'], NOTES[data['i']]), 
                                parse_mode = ParseMode.MARKDOWN,
                                reply_markup = InlineKeyboardMarkup(keyboard))
        
    # Check if the user pressed a button to perform an action on an alert.
    if data['type'] == 'act':
        
        # Check the all the possible actions
        
        if data['act'] == 'edit':
            
            # Keyboard to choose whether we want to edit the note or the description
            keyboard = [[InlineKeyboardButton('Edit note', callback_data="{'type':'act', 'act':'editN', 'i':" + str(data['i']) + ", 'list':'" + str(data['list']) + "'}"),
                         InlineKeyboardButton('Edit description', callback_data="{'type':'act', 'act':'editD', 'i':" + str(data['i']) + ", 'list':'" + str(data['list']) + "'}")],
                        [InlineKeyboardButton('Back', callback_data="{'type':'act', 'act':'back', 'list':'" + str(data['list']) + "'}"),
                         InlineKeyboardButton('Cancel', callback_data="{'type':'act', 'act':'cancel'}")]]
            
            query.edit_message_text(text=messageNoteText(data['list'], NOTES[data['i']]),
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup = InlineKeyboardMarkup(keyboard))
        
        elif data['act'] == 'editN':
            # Set to true the boolean variable to edit a note
            BOOL_EDIT_NOTE = True
            # Store the index and the list of the note in the global variables
            INDEX_NOTE = data['i']
            LIST_NOTE = data['list']
            # Store the ID of the previous message, so it can be modified later
            MESSAGE_ID_EDIT = query.message.message_id
            
            keyboardEdit = [[InlineKeyboardButton('Cancel', callback_data="{'type':'act', 'act':'cancel'}")]]
            # Prompt the user to write the new text for the alert.
            query.edit_message_text(text=messageNoteText(data['list'], NOTES[data['i']]) + '\n\nWrite the new note.',
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboardEdit))
        
        elif data['act'] == 'editD':
            # Set to true the boolean variable to edit a note
            BOOL_EDIT_NOTE_DESCR = True
            # Store the index and the list of the note in the global variables
            INDEX_NOTE = data['i']
            LIST_NOTE = data['list']
            # Store the ID of the previous message, so it can be modified later
            MESSAGE_ID_EDIT = query.message.message_id
            
            keyboardEdit = [[InlineKeyboardButton('Cancel', callback_data="{'type':'act', 'act':'cancel'}")]]
            # Prompt the user to write the new text for the alert.
            query.edit_message_text(text=messageNoteText(data['list'], NOTES[data['i']]) + '\n\nWrite the new description.',
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboardEdit))
        
        elif data['act'] == 'alert':
            # Set to true the boolean variable to set an alert.
            BOOL_SET_ALERT = True
            # Store the index and the list of the note in the global variables
            INDEX_NOTE = data['i']
            LIST_NOTE = data['list']
            # Store the ID of the previous message, so it can be modified later
            MESSAGE_ID_EDIT = query.message.message_id
            
            keyboardEdit = [[InlineKeyboardButton('Cancel', callback_data="{'type':'act', 'act':'cancel'}")]]
            # Prompt the user to write the new text for the alert.
            query.edit_message_text(text=messageNoteText(data['list'], NOTES[data['i']]) + '\n\nWrite the time for the alert.',
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboardEdit))
        
        elif data['act'] == 'delete':
            
            '''IMPLEMENT'''
        #     # Add this alert to the file with the sent alerts, so it is ignored when
        #     # downloading the backup.
        #     # Notice that the alerts have to be passed as a list
        #     updateSentAlerts((alerts[int(data['index'])],), FILE_ALERTS_SENT)
            
            # Remove this note from the list
            NOTES.remove(NOTES[int(data['i'])])
            # Write the edited list of notes to the file
            updateNotes(FILE_PREFIX, data['list'], NOTES)
            
            # Show again the keyboard with the list of notes
            query.edit_message_text("Notes in *{}* list, edited:".format(data['list']), parse_mode=ParseMode.MARKDOWN, 
                                      reply_markup = keyboardNotesList(NOTES, data['list'])) 
        
            
        elif data['act'] == 'back':
            # Show again the keyboard with the list of notes
            query.edit_message_text("Notes in *{}* list:".format(data['list']), parse_mode=ParseMode.MARKDOWN, 
                                      reply_markup = keyboardNotesList(NOTES, data['list'])) 
            
        elif data['act'] == 'cancel':
            # Delete this message
            query.bot.delete_message(query.message.chat_id, query.message.message_id)
            # Set the boolean variables to edit or to program alerts to false
            BOOT_SET_ALERT = False
            BOOL_EDIT_NOTE = False
            BOOL_EDIT_NOTE_DESCR = False


#def manageCommandFunction(update, context):
    #'''This will read the messages that start with / and are not one of the commands
    #defined previously.
        #If it is /<list>: add something to the list.
        #If it is /<list>s: view everything in the list, as a keyboard.
        #Otherwise, reply with a message of 'Unknown command or list'.
    #'''
    ## Get the first element of the message, without the '/', which is the first character
    #command = update.message.text.split(' ')[0][1:].lower()
    
    ## Check if the command is in the list of lists
    #if command in LISTS:
        #try:
            ## The rest of the message is the text
            #text = update.message.text.split(' ', 1)[1].strip()
            
            ## Try to find a description, separated from the main text by the first \n.
            #try:
                #text, description = text.split('\n', 1)
            #except ValueError:
                ## There was no description
                #description = None
                #pass
            
            ## If the text contains a comma, it cannot be stored in the csv file
            #if ',' in text:
                #update.message.reply_text('The text cannot contain any comma.')
                #return
            
            ## Add the text to the list
            #addNote(FILE_PREFIX, listname=command, text=text, description=description)
            ## Notify the user
            #update.message.reply_text('Note saved successfully.')
            
        #except IndexError:
            ## If there is no more text than the command, notify the user.
            #update.message.reply_text('You should write the text for the note.')
        
    ## Check if the command minus the last letter (which would be an 's') is in the list of lists
    #elif command[:-1] in LISTS:
        #'''IMPLEMENT'''
        ## Send the user a message with all the notes in the list.
        #checkNotesList(update, context, command[:-1])
    
    ## If the command does not correspond to any list, notify the user.    
    #else:    
        #update.message.reply_text('List unknown.')
        


#####################   TEXT RECOGNITION   ######################

    
def listenTextFunction(update, context):
    '''When any text message is received, the bot will reply telling the user
    what they have to clean this week.
    If it is Friday, Saturday, Sunday or Monday, they will give the option to 
    flag the task as done.'''
    update.message.reply_text(text='Tócache limpar *adlkf*', parse_mode=ParseMode.MARKDOWN)
        


##############################################################

# Add the handlers for the commands defined above
updater.dispatcher.add_handler(CommandHandler('start', startFunction))
updater.dispatcher.add_handler(CommandHandler('stop', stopFunction))
updater.dispatcher.add_handler(CommandHandler('help', helpFunction))
# MessageHandler with a command filter to reply to all commands that were not 
# recognized by the previous handlers.
#updater.dispatcher.add_handler(MessageHandler(Filters.command, manageCommandFunction))

## Add the handler for clicks in the buttons of inline keyboards
updater.dispatcher.add_handler(CallbackQueryHandler(inlineButtonPress))

## Add the handler for reading text
updater.dispatcher.add_handler(MessageHandler(Filters.text, listenTextFunction))





# Notify the user that the bot is working
updater.dispatcher.bot.send_message(chat_id = CHAT_ID, text = "Aquí Poza de Bar!")



## Start the process that looks for alerts that are due and sends the messages
## to the user
## This is stopped with the /stop command, by the line sendAlertsProcess.stop()
## in the function shutdown()
## I also add sendAlertsProcess.stop() at the end of the code, so this is stopped
## if I press Ctrl+C
# sendAlertsProcess = myTimer(sendAlerts, wait_seconds = ALERTS_TIME_INTERVAL,
#                             args = (updater, CHAT_ID, FILE_ALERTS, FILE_ALERTS_SENT, 
#                                     BACKUPS_HOURS_INTERVAL, ParseMode.MARKDOWN))
#
# #sendAlertsProcess = threading.Timer(ALERTS_TIME_INTERVAL, sendAlerts)
# sendAlertsProcess.start()

# Start the bot
updater.start_polling()

# Keep the bot executing until pressing Ctrl+C
updater.idle()

# Stop the process that sends the alerts.
sendAlertsProcess.stop()




# Stop the bot
# updater.stop()
