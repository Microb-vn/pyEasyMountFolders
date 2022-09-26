#!/usr/bin/python3
import os
import sys
import json
import argparse
import platform
import subprocess
import colorama
from colorama import Fore

def get_arguments():
    # Get Commandline Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-RefreshCredentials')
    parser.add_argument('-MappingsFile')
    args=parser.parse_args()

    # print(args.RefreshCredentials)
    # print(args.MappingsFile)
    return args.RefreshCredentials, args.MappingsFile

def check_folder(folder, action):
    # See if folder exists, is empty and is writeable and/or can be created
    # When the action is 'verify', a check is done whether the folder is available and empty and/or can be created
    # When the action is 'create', the folder will be checked, and if missing it will be created
    # The function returns "Ok" if all looks good
    folderparts = folder.split("/")
    errortext = "ERROR: Found path to validate: '" + folder + "'"

    if len(folderparts) < 2:
        return errortext + "; Path must at least be one level deep (e.g. /mnt or special/rob"

    if folderparts[0] == "":
        folderroot = "/"
    else:
        folderroot = os.getcwd() + "/"
        folderparts.insert(0,folderroot)

    for folderpart in folderparts[+1:]:
        # Loop thru list. First see if root exists
        if not os.path.exists(folderroot):
            return errortext + ", but cannot find '" + folderroot + "'" 

        pathtotest = folderroot + folderpart + "/"
        # Does the path exist?
        if not os.path.exists(pathtotest):
            if not os.access(folderroot, os.X_OK | os.W_OK): # Can we write to the folder?
                return errortext + "; the path '" + pathtotest.rstrip('/') + "' does not exist yet, but cannot create it: you're not authorized to write to '" + folderroot + "'"
            else:
                if action.upper() == "VERIFY":
                    return "Ok"
                else:
                    os.mkdir(pathtotest.rstrip('/'), mode=0o774 )

        folderroot = pathtotest
    # End of for loop

    # We are in the target folder. Is it empty?
    checkdir = os.listdir(folderroot)
    if not len(checkdir) == 0:
        return errortext + "; the found folder '" + folderroot + "' is not empty, so it cannot be used as target for file-mounts"

    return "Ok"

def processfile(file):
    try:
        action = 'open settings file ' + file
        with open(file, mode ='r')as infile:
            action = 'interpret json settings file ' + file + '; the json syntax is invalid, please check!'
            fileContent = json.load(infile)
            action = 'extract the mappings from json settings file ' + file + '; the object -Mappings- is not found in the file.'
            mappings = fileContent["Mappings"]
    except:
        return 'ERROR: Error occured while attemtping to ' + action

    if len(mappings) == 0:
        return 'ERROR: Did not find any items in the json mappings object in file ' + file + ';please check'

    itemcount = 0
    for mapping in mappings:
        itemcount = itemcount + 1
        action = 'attempt to extract values in mappings item in file ' + file + ' for item # ' + str(itemcount)

        actionLocalFolder = action + '; checking LocalFolder parameter'
        try:
            work = mapping["LocalFolder"]
        except:
            return "Error: while making an " + actionLocalFolder + "; parameter not found"
        if not work:
            return "Error: while making an " + actionLocalFolder + "; parameter is empty"
        
        # Does the local folder exist, and is it writable and empty (or can it be created if it doesnt exist yet)?
        result = check_folder(work, 'Verify')
        if not result == "Ok":
            return "Error: while making an " + actionLocalFolder + "; folder does not exist and/or is not writeable"

        actionRemoteHost = action + '; checking RemoteHost parameter'
        try:
            work = mapping["RemoteHost"]
        except:
            return "Error: while making an " + actionRemoteHost + "; parameter not found"
        if not work:
            return "Error: while making an " + actionRemoteHost + "; parameter is empty"

        actionRemoteFolder = action + '; checking RemoteFolder parameter'
        try:
            work = mapping["RemoteFolder"]
        except:
            return "Error: while making an " + actionRemoteFolder + "; parameter not found"
        if not work:
            return "Error: while making an " + actionRemoteFolder + "; parameter is empty"
    
    return mappings

def unmount_all():
    mount_result = subprocess.getoutput(
        "sudo mount | grep 'type cifs'")
    if not mount_result:
        return "Ok"
    
    mount_results = mount_result.split('\n')
    for mount_result in mount_results:
        uncEnd = mount_result.find(' on ')
        mountPointEnd = mount_result.find(' type cifs ')
        if uncEnd == -1 or mountPointEnd == -1:
            return "ERROR: Could not determine if cifs mounts already exist; last seen error: " + mount_result
        unc = mount_result[:uncEnd]
        mountPointBegin = uncEnd + 4
        mountPoint = mount_result[mountPointBegin:mountPointEnd]

        print('-' + unc + '-')
        print('-' + mountPoint + '-')
        try:
            umount_result = subprocess.getoutput(
                f"sudo umount " + mountPoint)
            if umount_result:
                return "ERROR: Could not unmount network drive from " + mountPoint + "; " + umount_result
        except:
            dummy = None
    return "Ok"

def getcredentials(scriptCacheFolder, user, remoteHost):
    fileName = f"{scriptCacheFolder}/{user}.{remoteHost}.file"


    return 'Ok'

def main():
    # Is it linux? If yes, we're good to go
    currentPlatform = platform.system()
    if currentPlatform != 'Linux':
        raise Exception('ERROR:Platform is not supported.')
    
    print("INFO: Script " + os.path.basename(__file__) + " is triggered, Starting its execution now...")
    print("INFO: Checking logged in user")

    user = os.getenv("SUDO_USER")
    if user is None:
        user = os.getenv("USER")
        print("INFO: Normal user " + user + " found;\033[1;32m expect a sudo password login during this script execution!\033[1;0m")
    elif user is None:
        raise Exception('ERROR:Current user is None.')
    else:
        print("INFO: Super user " + user + " found.")

    # Get Commandline Arguments
    refresh, file = get_arguments()

    # Set foldernames
    scriptFolder = os.path.dirname(__file__)
    scriptSettingsFolder = scriptFolder.replace("/.py","")
    scriptCacheFolder = scriptFolder.replace("/.py","/.cache")
    print("INFO: Checking required working directory " + scriptCacheFolder )
    if not os.path.isdir(scriptCacheFolder):
        try:
            os.mkdir(scriptCacheFolder, mode=0o774)
        except:
            raise Exception("ERROR: Cannot create a required working directory " + scriptCacheFolder + ". Please fix the issue and try again.")
    print("INFO: Working directory is available")

    # Set default parameters (if required)
    if not refresh:
        refresh = 'No'
    if not file:
        file = 'folders.default.json'

    # Validate the refresh parameter
    urefresh = refresh.upper()
    if not urefresh in ['YES', 'NO']:
        raise Exception('ERROR:Invalid RefreshCredentials parameter value found -' + refresh + '-; Should be either -Yes- or -No-.') 
    
    print("INFO: Based on trigger command used, the script assumes that -RefreshCredentials " + refresh + " and -MappingsFile " + file + " is to be used.")

    file = scriptSettingsFolder + "/" + file
    # Read the file and check its contents
    mappings = processfile(file)
    if type(mappings) is str:
        raise Exception(mappings)
        return
    
    # mappings now contains a list with items with fields:
    # - LocalFolder
    # - RemoteHost
    # - RemoteFolder
    result = unmount_all()
    if result != 'Ok':
        raise Exception(result)

    # Try to execute the mappings
    for mapping in mappings:
        # find the userID & password for that particular mapping
        credentials = getcredentials(scriptCacheFolder, user, mapping['RemoteHost'])
        if type(credentials) is str:
            raise Exception(credentials)
        

    # Check the password file(s)
    """
    Password files are in the cache folder and are named currentUserID.host.file, where:
        currentUserID is the currently logged in user
        host is the host the login onfo can be used for
    The files' content is 
        userid
        password
    
    files are secured and can ONLY be read by the person who created it.
    
    The files are checked for all hosts found in the mappings list
    """
    # ######################################




    # #### REMEMBER to clear the history entries where passwords occur #####


    return
   # Testing
    folder = "/xhome/rob"
    result = check_folder(folder, "create")
    print(result)
    return
    #End Testing



if __name__ == '__main__':
    main()