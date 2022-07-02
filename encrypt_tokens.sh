#!/bin/bash

# # The following will make all lines below it exit the execution if they fail
# set -e

# # Get the location of the current script
# SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}"; )" &> /dev/null && pwd 2> /dev/null; )";

# Read the passphrase from the file
PASSPHRASE="$(cat passphrase_encryption.txt)"

# If the passphrase is empty, exit the execution
if [ -z "$PASSPHRASE" ]
then
    echo
    echo "You need to write the passphrase in passphrase_encryption.txt"
    exit 1
fi

# Encrypt the dropbox token file
echo "Encrypting the token for the dropbox app..."
gpg -c --batch --passphrase $PASSPHRASE --output dropbox_token.gpg dropbox_token

# Encrypt the token files for the different bots
for BotDir in ./Bots/*;
do
    echo "Encrypting the token in $BotDir..."
    gpg -c --batch --passphrase $PASSPHRASE --output $BotDir/token.gpg $BotDir/token
    gpg -c --batch --passphrase $PASSPHRASE --output $BotDir/dropbox_token.gpg $BotDir/dropbox_token
done

# Encrypt the token files for the different test scripts
gpg -c --batch --passphrase $PASSPHRASE --output ./Test_Dropbox/dropbox_token.gpg ./Test_Dropbox/dropbox_token
gpg -c --batch --passphrase $PASSPHRASE --output ./Test/token.gpg ./Test/token
