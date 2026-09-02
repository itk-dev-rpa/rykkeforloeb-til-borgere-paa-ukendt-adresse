# Rykkerforløb til borgere på ukendt adresse

## Intro

The purpose of this robot is to send reminders to people with an unknown address to
contact Citizen's Service.

## Process

The robot roughly follows the following steps:

1. Look up any people over the age of 18 on an unknown address.
2. Check if they have a workable case in Kmd Nova.
3. If a reminder is due, send it using Digital Post and NemSMS.
4. Make a note of whether the reminder was sent or not.

The robot tracks its progress using the notes created in Nova.

## Known issues

KMD Nova and Kombit SF1601 might be unstable at times.

No errors are unrecoverable. Worst case we send duplicate letters
which doesn't matter.
