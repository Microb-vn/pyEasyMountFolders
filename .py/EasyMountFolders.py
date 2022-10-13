#!/usr/bin/python3
import os
import json
import argparse
import platform
import subprocess
import getpass
import time

def get_arguments():
    # Get Commandline Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-MappingsFile')
    parser.add_argument('-DisconnectOnly',choices=('True','False'))
    args=parser.parse_args()

    # print(args.MappingsFile)
    return args.MappingsFile, args.DisconnectOnly

def check_folder(folder, action):
    # See if folder exists, is empty and is writeable and/or can be created
    # When the action is 'verify', a check is done whether the folder is available and empty and/or can be created
    # When the action is 'create', the folder will be checked, and if missing it will be created
    # The function returns "Ok" if all looks good
    folderparts = folder.split("/")
    errortext = "ERROR: Found path to validate: '" + folder + "'"

    if len(folderparts) < 2:
        return errortext + "; Path must at least be one level deep (e.g. /mnt, ~/mnt or special/rob"

    if folderparts[0] == "":
        folderroot = "/"
    elif folderparts[0] == "~":
        folderroot = f"{os.path.expanduser('~')}/"
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
            return "Error: while making an " + actionLocalFolder + "; folder does not exist, is not empty or is not writeable"

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
    print("INFO: Start the unmount of previously mounted drives")
    mount_result = subprocess.getoutput(
        "mount | grep 'type cifs'")
    if not mount_result:
        print("INFO: No drives found to unmount")
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

        print(f"INFO: Unmounting network share {unc} from mountpoint {mountPoint}")
        try:
            umount_result = subprocess.getoutput(
                f"sudo umount -t cifs " + mountPoint)
            if umount_result:
                return "ERROR: Could not unmount network drive from " + mountPoint + "; " + umount_result
        except:
            dummy = None
    return "Ok"

def getcredentials(scriptCacheFolder, user, remoteHost):
    fileName = f"{scriptCacheFolder}/{user}.{remoteHost}.file"
    # Details of the password file(s)
    """
    Password files are in the cache folder and are named currentUserID.host.file, where:
        currentUserID is the currently logged in user
        host is the host the login info can be used for
    The files' content is 
        userid
        password
    
    files are secured and can ONLY be read by the person who created it.
    """
    if not os.path.exists(fileName):
        userId, password = askforcredentials(f"INFO: There is no (valid) credentialsfile for host {remoteHost}", remoteHost)
        if userId.startswith("ERROR: "):
            return userId
        outfile = open(fileName, "w")
        outfile.write(f"{userId}\n")
        outfile.write(f"{password}\n")
        outfile.close()
        # secure the file
        subprocess.call(['chmod', '0600', fileName])
    else:
        # open the file and read content
        outfile = open(fileName, "r")
        userId = outfile.readline().strip()
        password = outfile.readline().strip()
        if userId == "" or userId == None or password == "" or password == None:
            return f"ERROR: Invalid credentialsfile found: {fileName}. Please remove it and try to run the script again."
    return userId, password

def askforcredentials(reason, remoteHost):
    print(f"{reason}; please input the (full) user ID and password to connect to {remoteHost}.")
    while True:
        userId = input("QUESTION: Enter the userID that can be used: ")
        if userId == None:
            print("WARNING: No input detected, please try again...")
            continue
        break
    while True:
        password = getpass.getpass(prompt=f'QUESTION: Enter the password that can be used for user {userId}: ',stream=None)
        if password == None or password == '':
            print("WARNING: No input detected, please try again...")
            continue
        break
    return userId, password

def detect_host(host):
    # ping the host
    response = os.system("ping -c 1 " + host + " > /dev/null 2>&1")

    # and then check the response...
    if response == 0:
        return True
    else:
        return False


def main():
    # ===============
    # CHECK PLATFORM: Is it linux? If yes, we're good to go
    # ===============
    currentPlatform = platform.system()
    if currentPlatform != 'Linux':
        raise Exception('ERROR:Platform is not supported.')
    
    print("INFO: Script " + os.path.basename(__file__) + " is triggered, Starting its execution now...")
    print("INFO: Checking logged in user")

    # ===========
    # CHECK USER: Ok if a user is logged in
    # ===========
    user = os.getenv("SUDO_USER")
    if user is None:
        user = os.getenv("USER")
        print("INFO: Normal user " + user + " found;\033[1;32m expect a sudo password login during this script execution!\033[1;0m")
    elif user is None:
        raise Exception('ERROR:Current user is None.')
    else:
        print("INFO: Super user " + user + " found.")
    uid = os.getuid()
    gid = os.getgid()

    # =========================
    # GET COMMANDLINE ARGUMENTS and set important literals
    # =========================
    file, disconnectOnly = get_arguments()

    scriptFolder = os.path.realpath(os.path.dirname(__file__))
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
    if not file:
        file = 'folders.default.json'
    if not disconnectOnly:
        disconnectOnly = False
    elif disconnectOnly.upper() == 'TRUE':
        disconnectOnly = True
    else:
        disconnectOnly = False

    print("INFO: Based on trigger command used, the script assumes that -MappingsFile " + file + " and -DisconnectOnly " + str(disconnectOnly) + " is to be used.")

    # #######################
    # UNMOUNT ALL CIFS DRIVES
    # #######################
    result = unmount_all()
    if result != 'Ok':
        raise Exception(result)
    
    if disconnectOnly:
        sleepTime = 5
        print("INFO: Disconnect only was requested. Done!  This window will close in {sleepTime} seconds")
        time.sleep(sleepTime)
        return

    # #################
    # READ SETTINGSFILE and check its content
    # #################
    file = scriptSettingsFolder + "/" + file
    # Read the file and check its contents
    print("INFO: Checking the contents of " + file)
    mappings = processfile(file)
    if type(mappings) is str:
        raise Exception(mappings)
        return
    print("INFO: No anomalies found in " + file)
    
    # mappings now contains a list with items with fields:
    # - LocalFolder
    # - RemoteHost
    # - RemoteFolder
    
    # ###########################
    # Try to execute the mappings
    # ###########################
    print("INFO: Start creating the drive mappings")
    for mapping in mappings:
        # See if host is available in the network
        print(f"INFO: Checking host {mapping['RemoteHost']}")
        result = detect_host(mapping["RemoteHost"])
        if not result:
            print(f"INFO: Host {mapping['RemoteHost']} is not detected/does not respond on this network")
            continue

        # find the userID & password for that particular mapping
        while True:
            # Credentials loop
            print(f"INFO: Found; getting the credentials for host {mapping['RemoteHost']} to create mapping to remote folder {mapping['RemoteFolder']}")
            credentials = getcredentials(scriptCacheFolder, user, mapping['RemoteHost'])
            if type(credentials) is str:
                raise Exception(credentials)

            # Check if target folder exists (again); but now create it if required
            result = check_folder(mapping['LocalFolder'], 'Create')
            if result != 'Ok':
                raise Exception(result)
            
            # Set question variable to default value
            question = "X"
            # Issue command to create the mapping
            while True:
                # Mount loop
                try:
                    print(f"INFO: Attemtping to map remote folder to {mapping['LocalFolder']}")
                    mount_result = subprocess.getoutput(
                        f"sudo mount -t cifs -o username={credentials[0]},password={credentials[1]},uid={uid},gid={gid} //{mapping['RemoteHost']}/{mapping['RemoteFolder']} {mapping['LocalFolder']} ")
                except:
                    raise Exception(f"ERROR: Could not mount network drive //{mapping['RemoteHost']}/{mapping['RemoteFolder']}; reason unknown... ")

                if mount_result.find("mount error") != -1:
                    if mount_result.find('Permission denied') != -1:
                        print("WARNING: The mount command failed, permission was denied")
                        print("QUESTION: What you want me to do?")
                        print("QUESTION: r) retry the mount operation")
                        print("QUESTION: c) retry the mount operation with other credentials")
                        print("QUESTION: q) quit script execution")
                        while True:
                            # Question loop
                            question = input("QUESTION: enter your choice (r, c or q):")
                            if question.upper() == 'Q':
                                print("INFO: Quiting script execution")
                                return
                            elif question.upper() == 'R':
                                print( "INFO: Retrying the mount operation")
                                break # get out of the question loop
                            elif question.upper() == "C":
                                print("INFO: Retrying the mount operation with new credentials")
                                fileName = f"{scriptCacheFolder}/{user}.{mapping['RemoteHost']}.file"
                                os.remove(fileName)
                                break # Get out of the question loop
                            else:
                                print("ERROR: Invalid input!")
                                continue # do the question loop again
                            break # the question loop
                        if question.upper() == "R":
                            continue # do the mount again
                        else:
                            break # get out of the mount loop

                    raise Exception(f"ERROR: Could not mount network drive //{mapping['RemoteHost']}/{mapping['RemoteFolder']}; {mount_result}".replace('\n', '!'))
                print(f"INFO: mapping action executed, network folder is now available in {mapping['LocalFolder']}")
                break # Break out of mount loop
            if question.upper() == "C":
                continue # the credentials loop
            break # Break out the credentails loop
    
    # print("# #### REMEMBER to clear the history entries where passwords occur #####") - rob: no need, the 'inline' cmds are not captured

    sleepTime = 5
    print(f"INFO: Done! This window will close in {sleepTime} seconds")
    time.sleep(sleepTime)
    
    return

if __name__ == '__main__':
    main()