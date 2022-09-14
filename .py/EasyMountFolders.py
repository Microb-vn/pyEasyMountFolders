#!/usr/bin/python3
import os
import sys
import argparse

print("this is script .py")

def get_arguments():
    # Get Commandline Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-RefreshCredentials')
    parser.add_argument('-MappingsFile')
    args=parser.parse_args()

    print(args.RefreshCredentials)
    print(args.MappingsFile)
    return args.RefreshCredentials, args.MappingsFile

def check_folder(folder, action):
    # See if folder exists, is empty and is writeable and/or can be created
    # When the action is 'verify', a check is done of the folder is available and empty and/or can be created
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
                if action == "verify":
                    return "Ok"
                else:
                    os.mkdir(pathtotest.rstrip('/'), mode=0o774 )

        folderroot = pathtotest

    # We are in the target folder. Is it empty?
    checkdir = os.listdir(folderroot)
    if not len(checkdir) == 0:
        return errortext + "; the found folder '" + folderroot + "' is not empty, so not a valid target for file-mounts"

    return "Ok"
        


def main():
    # Testing
    folder = "/xhome/rob"
    result = check_folder(folder, "create")
    print(result)
    return
    #End Testing


    # Get Commandline Arguments
    refresh, file = get_arguments()

    print(refresh)
    print(file)

if __name__ == '__main__':
    main()