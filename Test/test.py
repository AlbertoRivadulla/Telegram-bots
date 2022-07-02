#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 18:42:05 2020

@author: alberto
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
from telegram import KeyboardButton, ReplyKeyboardMarkup, ParseMode
import logging

import threading # Needed for the \stop command
from subprocess import Popen, PIPE # Needed for the \battery command
from socket import socket, AF_INET, SOCK_DGRAM # Needed for the \localIP command

from telegram.error import NetworkError

# Read the tokens
TOKEN = ''
CHAT_ID = ''
with open("token", "r") as f:
    # The information in the first two lines is not important
    for i in range(2):
        f.readline()
    # The third line is the token
    TOKEN = f.readline().strip()

# The Updater class continuously fetches new updates from telegram and passes 
# them on to the Dispatcher class
updater = Updater(token=TOKEN, 
                  use_context=True)


# The Dispatcher is created automatically with the Updater.
# For quicker access, we can introduce it locally
dispatcher = updater.dispatcher

# Set up the logging module, so you will know when things don't work as expected
# This is used to print in the terminal the errors that are not caused by the 
# Telegram API (eg, Python errors)
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
        
dispatcher.add_error_handler(error_callback)



##################   COMMANDS   ##########################    

# Define a function that should process a specific type of update
def start(update, context):
    print("start command")
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Hi. I'm a bot, please talk to me!")
    print("Chat id: {}".format(update.effective_chat.id))

# The goal is to have this function called every time the Bot receives a Telegram 
# message that contains the /start command. 
# To accomplish that, you can use a CommandHandler and register it in the dispatcher
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


######################

# Implement a /caps command that will take some text as an argument and reply 
# to it in capital letters. 
# You can receive the arguments (as a list, split on spaces) that were passed 
# to a command in the callback function
def caps(update, context):
    print(context.args)
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)


#######################

# Function to stop the execution of the bot.
def shutdown():
    print("Stopping bot...")
    updater.stop()
    updater.is_idle = False
    
# The following function is called with the /stop command
# It executes shutdown() in a new thread, stopping the execution of the bot
def stop(update, context):
    threading.Thread(target = shutdown).start()
    
    update.message.reply_text(text = 'Stopping bot...')
    
stop_handler = CommandHandler('stop', stop)
dispatcher.add_handler(stop_handler)



#######################

# Function to show the battery of the laptop
def battery(update, context):
    # Get the battery percentage and charging status.
    percentage = Popen('cat /sys/class/power_supply/BAT0/capacity'.split(), 
                                  stdout=PIPE).communicate()[0].decode('ascii')
    status = Popen('cat /sys/class/power_supply/BAT0/status'.split(), 
                              stdout=PIPE).communicate()[0].decode('ascii')

    # Send the results in a well formatted message.
    context.bot.send_message(chat_id = update.effective_chat.id,
                             text = 'Battery percentage: {} %\n{}'.format(percentage[:-1],
                                                                           status[:-1]))

# Make a command handler, and register it in the dispatcher.
battery_handler = CommandHandler('battery', battery)
dispatcher.add_handler(battery_handler)



#######################

# Function to show the local IP address of the laptop
def localIP(update, context):
    # Show the status of the bot as typing...
    context.bot.send_chat_action(chat_id = update.effective_chat.id, 
                                 action = ChatAction.TYPING)
    
    # Open a connection with '8.8.8.8' in port 80 (Google's public DNS)
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    # Print the IP address
    # print(s.getsockname()[0])
    # print(s.getsockname())
    localIPaddress = s.getsockname()[0]
    s.close()
    
    # Send the results in a well formatted message.
    context.bot.send_message(chat_id = update.effective_chat.id,
                             text = 'Local IP address: {}'.format(localIPaddress))
    # The following code sends the same message in the chat:
    # update.message.reply_text(text = 'Local IP address: {}'.format(localIPaddress))

# Make a command handler, and register it in the dispatcher.
localIP_handler = CommandHandler('localIP', localIP)
dispatcher.add_handler(localIP_handler)



#####################   TEXT RECOGNITION   ################

# MessageHandler with a command filter to reply to all commands that were not 
# recognized by the previous handlers.
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)



# Let's add another handler that listens for regular messages. 
# Use the MessageHandler, to echo all text messages
def echo(update, context):
    # Append something to the text
    input_text = update.message.text
    text_to_output = input_text + ' e algo mais'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_to_output)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)



# To send a message to the chat:
dispatcher.bot.send_message(chat_id = '482306343', text = "Test message")

# Start the bot
updater.start_polling()

# Keep the bot executing until pressing Ctrl+C
updater.idle()


# Stop the bot
# updater.stop()

