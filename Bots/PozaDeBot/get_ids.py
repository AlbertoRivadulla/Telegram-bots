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

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
#from telegram import ChatAction
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

# File where the IDs will be stored.
FILE_IDS = './Files/IDs.txt'

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


#####################   TEXT RECOGNITION   ######################

    
def listenTextFunction(update, context):
    '''When any text message is received, the bot will simply store the user's ID in the file,
    if it is not already there.'''
    
    try:
        # Get the user's name and their ID
        user_info = ';'.join((update.message.chat.first_name, str(update.message.chat.id)))
        
        # Read the file with IDs
        with open(FILE_IDS, 'r') as f:
            file_contents = f.read().split('\n')
        print(file_contents)
        # Check if the current id is in the file
        if user_info in file_contents:
            update.message.reply_text(text='Non te pases 😪')
        else:
            # Add the user data to the file
            with open(FILE_IDS, 'a') as f:
                f.write(user_info + '\n')
            # Notify the user
            update.message.reply_text(text='Guai! 👍')
    
    except:
        # Tell the user something went wrong
        update.message.reply_text(text='Algo foi mal...')


##############################################################

# Add the handlers for the commands defined above
updater.dispatcher.add_handler(CommandHandler('start', startFunction))
updater.dispatcher.add_handler(CommandHandler('stop', stopFunction))
updater.dispatcher.add_handler(CommandHandler('help', helpFunction))
# MessageHandler with a command filter to reply to all commands that were not 
# recognized by the previous handlers.
#updater.dispatcher.add_handler(MessageHandler(Filters.command, manageCommandFunction))

## Add the handler for reading text
updater.dispatcher.add_handler(MessageHandler(Filters.text, listenTextFunction))

# Start the bot
updater.start_polling()

# Keep the bot executing until pressing Ctrl+C
updater.idle()
