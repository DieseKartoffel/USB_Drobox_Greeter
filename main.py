from __future__ import print_function
from os.path import exists
import sys
import os
import time
import argparse
import contextlib
import datetime
import six
import unicodedata


import dropbox
import config #local access token and settings file

TOKEN = config.TOKEN
FOLDER_NAME_DRIVE = config.USB_FOLDER    #name of the folder that is synchronized from the new drive to Dropbox
FOLDER_NAME_DROPBOX = config.DROPBOX_FOLDER
TICK_SPEED = config.REFRESH_TIME  #pause before scanning for a new drive in seconds

def drives():
    drive_list = []
    for drive in range(ord('A'), ord('N')):
        if exists(chr(drive) + ':'):
            drive_list.append(chr(drive))
    return drive_list

def hasDropbox(drive):
    ls = os.listdir(drive+":\\") #A:\
    return FOLDER_NAME_DRIVE in ls

def synchDropbox(drive):
    rootdir = drive+":\\"+FOLDER_NAME_DRIVE
    folder = FOLDER_NAME_DROPBOX
    dbx = dropbox.Dropbox(TOKEN)
    for dn, dirs, files in os.walk(rootdir):
        subfolder = dn[len(rootdir):].strip(os.path.sep)
        listing = list_folder(dbx, folder, subfolder)
        print('Descending into', subfolder, '...')
        print('Listing:\n',listing)
        # First do all the files.
        for name in files:
            fullname = os.path.join(dn, name)
            if not isinstance(name, six.text_type):
                name = name.decode('utf-8')
            nname = unicodedata.normalize('NFC', name)
            if name.startswith('.'):
                print('Skipping dot file:', name)
            elif name.startswith('@') or name.endswith('~'):
                print('Skipping temporary file:', name)
            elif name.endswith('.pyc') or name.endswith('.pyo'):
                print('Skipping generated file:', name)
            elif nname in str(listing):
                md = listing[nname]
                mtime = os.path.getmtime(fullname)
                mtime_dt = datetime.datetime(*time.gmtime(mtime)[:6])
                size = os.path.getsize(fullname)
                if (isinstance(md, dropbox.files.FileMetadata) and
                        mtime_dt == md.client_modified and size == md.size):
                    print(name, 'is already synced [stats match]')
                else:
                    print(name, 'exists with different stats, downloading')
                    res = download(dbx, folder, subfolder, name)
                    with open(fullname) as f:
                        data = f.read()
                    if res == data:
                        print(name, 'is already synced [content match]')
                    else:
                        path = str("/"+folder+"/"+subfolder.replace(os.path.sep, '/')+name)
                        print(path,"\n")
                        lastEditDpx = dbx.files_get_metadata(path).server_modified
                        systemTimeFormat = os.path.getmtime(fullname)
                        lastEditDrv = version_date = datetime.datetime.fromtimestamp(systemTimeFormat)
                        print(name, 'has changed since last sync');
                        print('Dropbox Edit At: ',lastEditDpx)
                        print('USB Edit At: ',lastEditDrv)
                        if(lastEditDrv < lastEditDpx):
                            print('USB version is latest - Uploading')
                            upload(dbx, fullname, folder, subfolder, name,
                                   overwrite=True)
                        else:
                            print('USB version is older - Overwriting with download')
                            f = open(fullname, 'wb') #open file in binary mode to overwrite easily
                            f.write(res)
                            f.truncate()
            else:
                print(name, 'New File Uploading')
                upload(dbx, fullname, folder, subfolder, name)

        # Then choose which subdirectories to traverse.
        keep = []
        for name in dirs:
            if name.startswith('.'):
                print('Skipping dot directory:', name)
            elif name.startswith('@') or name.endswith('~'):
                print('Skipping temporary directory:', name)
            elif name == '__pycache__':
                print('Skipping generated directory:', name)
            else:
                print('Keeping directory:', name)
                keep.append(name)
        dirs[:] = keep

def list_folder(dbx, folder, subfolder):
    """List a folder.
    Return a dict mapping unicode filenames to
    FileMetadata|FolderMetadata entries.
    """
    path = '/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'))
    while '//' in path:
        path = path.replace('//', '/')
    path = path.rstrip('/')
    try:
        with stopwatch('list_folder'):
            res = dbx.files_list_folder(path)
    except dropbox.exceptions.ApiError as err:
        print('Folder listing failed for', path, '-- assumed empty:', err)
        return {}
    else:
        rv = {}
        for entry in res.entries:
            rv[entry.name] = entry
        return rv

def download(dbx, folder, subfolder, name):
    """Download a file.
    Return the bytes of the file, or None if it doesn't exist.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    with stopwatch('download'):
        try:
            md, res = dbx.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
    data = res.content
    print(len(data), 'bytes; md:', md)
    return data

def upload(dbx, fullname, folder, subfolder, name, overwrite=False):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)
    with open(fullname, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx.files_upload(
                data, path, mode,
                client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                mute=True)
        except dropbox.exceptions.ApiError as err:
            print('*** API error', err)
            return None
    print('uploaded as', res.name.encode('utf8'))
    return res

@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))

if __name__ == '__main__':
    '''    dir = 'E'
    synchDropbox(dir)'''

    before = drives()
    while True:
        time.sleep(TICK_SPEED)
        after = drives()
        newDrives = [value for value in after if not value in before]
        if (newDrives):
            sys.stdout.write("New Drives added: " + str(newDrives) + "\n")
            for d in newDrives:
                if(hasDropbox(d)):
                    synchDropbox(d)
        else:
            sys.stdout.write("No new drive\n")
        sys.stdout.flush()
        before = after;

    print("The following drives exist:", drives2())
