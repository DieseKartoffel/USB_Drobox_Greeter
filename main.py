from os.path import exists
import sys
import os
import time


FOLDER_NAME = "Citavi"      #name of the folder that is synchronized from the new drive to Dropbox
TICK_SPEED = 5               #pause before scanning for a new drive in seconds

def drives():
    drive_list = []
    for drive in range(ord('A'), ord('N')):
        if exists(chr(drive) + ':'):
            drive_list.append(chr(drive))
    return drive_list

def dropbox(drive):
    ls = os.listdir(drive+":\\") #A:\
    return FOLDER_NAME in ls

def synchDropbox(drive):
    ls = os.listdir(drive+":\\"+FOLDER_NAME)
    print(ls)

before = drives()
while True:
    time.sleep(TICK_SPEED)
    after = drives()
    newDrives = [value for value in after if not value in before]
    if (newDrives):
        sys.stdout.write("New Drives added: " + str(newDrives) + "\n")
        for d in newDrives:
            if(dropbox(d)):
                synchDropbox(d)
    else:
        sys.stdout.write("No new drive\n")
    sys.stdout.flush()
    before = after;

print("The following drives exist:", drives2())
