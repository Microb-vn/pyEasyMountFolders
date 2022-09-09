#!/usr/bin/python3
import sys
import argparse

print("this is script .py")

def main():
    print("this is function main")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-file')
    parser.add_argument('-first')
    args=parser.parse_args()

    print(args.file)
    print(args.first)
