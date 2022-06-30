#!/usr/bin/python

# pip imports
from mtgsdk import Card
from mtgsdk import Set
# Add Pillow Here
# stdlib imports
import argparse, sys

# Globals for legibility
CARD_WIDTH = 226
CARD_HEIGHT = 320

help_splash = ''' Usage: bw-proxy [FILE]
    Given an infile of type txt, generate a printable pdf
    that contains imageless black & white proxies that
    the user can print.
'''
parser = argparse.ArgumentParser(description=help_splash,
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('infile', nargs='?', type=argparse.FileType('r'))

args = parser.parse_args()

def read_infile():
    if not args.infile:
        print('\nPlease specify input file!\n', file=sys.stderr)
        exit()
    with open(args.infile.name) as f:
        c_list = f.read().splitlines()
    c_list = [i for i in c_list if i] # strip empty lines
    decklist = []
    for c in c_list:
        data = c.split(' ', 1)
        print('Looking for: ', data[1], '...')
        card = Card.where(name=data[1]).all()
        decklist.append((data[0], card[0]))
        return decklist # debug
    return decklist

def main():
    deck = read_infile()
    for entry in deck:
        print(entry[0], entry[1].name)
if __name__ == '__main__':
    main()        
