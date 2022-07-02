#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 20:36:08 2020

@author: alberto
"""


# import sys
import dropbox
import os
import datetime

# from dropbox.files import WriteMode
# from dropbox.exceptions import ApiError, AuthError

# Read the access token
DROPBOX_TOKEN = ''
with open("dropbox_token", "r") as f:
    # Get the token from the 5th line
    for i in range(4):
        f.readline()
    DROPBOX_TOKEN = f.readline().strip()

LOCAL_FILE = './single_alerts.txt'
BACKUP_FILE = '/single_alerts_backup.txt' # Keep the forward slash before destination filename


# Uploads contents of LOCALFILE to Dropbox
def dropboxUpload(local_file = LOCAL_FILE, remote_file = BACKUP_FILE):
    '''Upload the contents of local_file to Dropbox.'''
    with open(local_file, 'rb') as f:
        # We use WriteMode=overwrite to make sure that the settings in the file
        # are changed on upload
        print("Uploading " + local_file + " to Dropbox as " + remote_file + "...")
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
                
                
def dropboxDownload(remote_file):
    '''Returns the binary data in the remote file, and its modification time as a 
    datetime.datetime object.'''
    try:
        md, res = dbx.files_download(remote_file)
        
    # except dropbox.exceptions.HttpError as err:
    #     print('HTTP error: ', err)
    #     return None, None
    except:
        print('Unable to download the remote file.')
        return None, None
    
    data = res.content
    # print(len(data), 'bytes; md:', md)
    print(md)
    return data, md.client_modified

def dropboxDownload_to_file(file_remote = BACKUP_FILE, file_local = LOCAL_FILE):
    '''Download a remote file to a local file.
        If the local file already exists, check the modification time. If it hasn't
        been modified after the remote file, then overwrite it. Otherwise don't.'''
    # Download the remote file
    remote_data, remote_mod_time = dropboxDownload(file_remote)
    
    # Check if the file has been downloaded successfully
    if remote_data:
        # Check if the local file already exists
        if os.path.exists(file_local):
            print('Local file exists!')
            '''
            
            This part is an example, and has to be modified for the AlertBot.
            
            '''
            print(remote_mod_time)
            # If it does, check if it has been modified later than the backup
            delta_mod_time = remote_mod_time - datetime.datetime.fromtimestamp(os.path.getmtime(LOCAL_FILE))
            if delta_mod_time.total_seconds() > 0:
                print('Local file is older. Overwriting.')
                # If it hasn't, overwrite it with the backup
                with open(file_local, 'wb') as f:
                    f.write(remote_data)
            else:
                print('Local file is newer.')
                # If it has, skip
                pass
        else:
            print('Local file does not exist.')
            # If it does not exist, download it
            with open(file_local, 'wb') as f:
                f.write(remote_data)

    return


#datetime.datetime.fromtimestamp(os.path.getmtime(LOCAL_FILE)) - d



# # Adding few functions to check file details
# def checkFileDetails():
#     print("Checking file details")

#     print("File list is : ")
    
#     for entry in dbx.files_list_folder('').entries:
#         print(entry.name)


if __name__ == '__main__':
    
    # Check for an access token
    if (len(DROPBOX_TOKEN) == 0):
        print("ERROR: Looks like you didn't add your access token. Open up backup-and-restore-example.py in a text editor and paste in your token in line 14.")

    # Create an instance of a Dropbox class, which can make requests to the API.
    print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except dropbox.exceptions.AuthError:
        print("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")
    
    # try:
    #     checkFileDetails()
    # except:
    #     print("Error while checking file details")

    print("Creating backup...")
    # Create a backup of the current settings file
    dropboxUpload(LOCAL_FILE, BACKUP_FILE)

    print("Done!")
    

