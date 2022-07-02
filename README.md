## Token files

I encrypt the files using

    gpg -c --batch --passphrase <passphrase> <file_in>

This produces the encrypted file `<file>.gpg`. The option `--batch` is needed so
that it does not prompt the user to enter the passphrase again.

To decrypt the files uploaded to Github, use

    gpg -d --batch --passphrase <passphrase> --output <file_out> <file_in_gpg>

Otherwise, I automated this in the bash scripts `encrypt_tokens.sh` and
`decrypt_token.sh`.

The format of the files is:

- Bot tokens:
        
        bot name
        bot username
        token

- Dropbox app:

        App name
        App folder name
        App key
        App secret
        Access token
