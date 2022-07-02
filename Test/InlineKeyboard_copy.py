#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic example for a bot that uses inline keyboards.
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update, context):
    # keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'),
    #              InlineKeyboardButton("Option 2", callback_data='2'),

    #             InlineKeyboardButton("Option 3", callback_data='3')]]
    
    keyboard = [[InlineKeyboardButton('Option {}'.format(i), callback_data=i)] 
                for i in range(1, 5)]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    

def button(update, context):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    
    print(query.data)
    
    print('Selected option: {}'.format(query.data))
    
    keyboard = [[InlineKeyboardButton('Edit', callback_data="{'a':'edit', 'b':2}"), 
                  InlineKeyboardButton('Duplicate', callback_data='duplicate'),
                  InlineKeyboardButton('Delete', callback_data='delete')],
                 [InlineKeyboardButton('Back', callback_data='back'),
                  InlineKeyboardButton('Cancel', callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    

    query.edit_message_text(text="Selected option: {}".format(query.data),
                            reply_markup = reply_markup)


def help(update, context):
    update.message.reply_text("Use /start to test this bot.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Read the tokens
    TOKEN = ''
    CHAT_ID = ''
    with open("token", "r") as f:
        # The information in the first two lines is not important
        for i in range(2):
            f.readline()
        # The third line is the token
        TOKEN = f.readline().strip()

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()