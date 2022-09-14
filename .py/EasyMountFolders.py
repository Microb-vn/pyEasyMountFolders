#!/usr/bin/python3
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
    # When the action is 'verify', the folder is available and empty and/or can be created
    # The function returns "Ok" if all looks good




def main():
    print("this is function main")
    # Get Commandline Arguments
    refresh, file = get_arguments()

    print(refresh)
    print(file)

if __name__ == '__main__':
    main()