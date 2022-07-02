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
    echo "You need to write the passphrase in passphrase.txt"
    exit 1
fi

# Decrypt the dropbox token file
echo "Decrypting the token for the dropbox app..."
gpg -d --batch --passphrase $PASSPHRASE --output dropbox_token dropbox_token.gpg

# Decrypt the token files for the different bots
for BotDir in ./Bots/*;
do
    echo "Decrypting the token in $BotDir..."
    gpg -d --batch --passphrase $PASSPHRASE --output $BotDir/token $BotDir/token.gpg
    gpg -d --batch --passphrase $PASSPHRASE --output $BotDir/dropbox_token $BotDir/dropbox_token.gpg
done

# Decrypt the token files for the different test scripts
# Encrypt the token files for the different test scripts
gpg -d --batch --passphrase $PASSPHRASE --output ./Test_Dropbox/dropbox_token ./Test_Dropbox/dropbox_token.gpg
gpg -d --batch --passphrase $PASSPHRASE --output ./Test/token ./Test/token.gpg
