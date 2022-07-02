#!/usr/bin/python

# pip imports
from mtgsdk import Card
from mtgsdk import Set
from PIL import Image, ImageDraw, ImageFont
# stdlib imports
import argparse, sys, math

# Globals for Scale (in future, add num per page?)
# For normal card: 226 x 320 px
# Page Card: 500 x 700
FONT_SIZE = 14
FONT_TYPE ='/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf'
CARD_WIDTH = 500 # * 2
CARD_HEIGHT = 700 # * 2
EDGE_SCALE = CARD_WIDTH / 80 
N_SCALE = CARD_HEIGHT / 20
T_SCALE = CARD_HEIGHT / 2.2
O_SCALE = CARD_HEIGHT / 1.9 

NUM_P_W = 3
NUM_P_H = 4
PAGE_W = CARD_WIDTH * NUM_P_W
PAGE_H = CARD_HEIGHT * NUM_P_H

# Other Globals & argparse
BASICS = ['Swamp', 'Forest', 'Mountain', 'Plains', 'Island'] 

help_splash = ''' Usage: bw-proxy [FILE]
    Given an infile of type txt, generate a printable pdf
    that contains imageless black & white proxies that
    the user can print.
'''
parser = argparse.ArgumentParser(description=help_splash,
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('infile', nargs='?', type=argparse.FileType('r'))

args = parser.parse_args()

# Functions
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
        c_name = data[1]
        if c[0] == '#' or len(c) == 0:
            continue
        if c_name in BASICS:
            continue
        print('Looking for: ', c_name, '...')
        cards = Card.where(name=data[1]).all()
        card = None
        for c in cards:
            if c_name == c.name:
                card = c
                continue
        if card is None:
            print('!!! Error: Could not find', c_name, '!!!', 
                file=sys.stderr)
        decklist.append((int(data[0]), card))
    return decklist

'''
    Text Scalar Algorithm was adapted from @Nachtalb at
    (https://stackoverflow.com/questions/4902198/
    pil-how-to-scale-text-size-in-relation-to-the-size-of-the-image)
'''
def text_scalar(text, font, img_size, img_fill = 0.95):
    jump_size = 2;
    font_size = 1
    overflow = img_fill * img_size
    while True:
        if font.getsize(text)[0] < overflow:
            font_size += jump_size
        else:
            jump_size = jump_size // 2
            font_size -= jump_size
        font = ImageFont.truetype(FONT_TYPE, font_size)
        if jump_size <= 1:
            if font_size > CARD_WIDTH / 11: # may be bad~44
                font_size = CARD_WIDTH // 11 
            return font_size

def add_name(d, card, font):
    cost = card.mana_cost
    if cost is None:
        cost = ''
    top = card.name + '    ' + cost
    n_size = text_scalar(top, font, CARD_WIDTH)
    d.text((EDGE_SCALE, N_SCALE), top, fill='black', anchor='ls', 
        font=ImageFont.truetype(FONT_TYPE, n_size))
    return d

def add_type(d, card, font):
    t_size = text_scalar(card.type, font, CARD_WIDTH)
    d.text((EDGE_SCALE, T_SCALE), card.type, fill='black', anchor='ls',
        font=ImageFont.truetype(FONT_TYPE, t_size))
    return d

def add_text(d, card, font):
    # 11 words max?
    text = card.text.splitlines()
    row = O_SCALE
    queue = []
    size = 999; # default
    for par in text:
        body = par.split()
        n_per_line = 6 if len(body) > 60 else 4
        while len(body) > 0:
            clip = min(len(body), n_per_line) 
            sub = ' '.join(body[0:clip])
            new_size = text_scalar(sub, font, CARD_WIDTH)
            size = min(new_size, size)
            queue.append(sub)
            body = body[clip:]
        queue.append('#BUFFER#')
    for l in queue:
        if l == '#BUFFER#':
            row += size
            continue
        d.text((EDGE_SCALE, row), l, fill='black', anchor='ls',
            font=ImageFont.truetype(FONT_TYPE, size))
        row += size

def card_image(card):
    print("Drawing....", card.name)
    font = ImageFont.truetype(FONT_TYPE, 1)
    cd = Image.new('1', (CARD_WIDTH, CARD_HEIGHT), 1) # 1=BW
    d = ImageDraw.Draw(cd)
    d = add_name(d, card, font)
    d = add_type(d, card, font)
    d = add_text(d, card, font)
    return cd

def main():
    deck = read_infile()
    # test = card_image(deck[0][1])
    pages = []
    page = Image.new('1', (PAGE_W, PAGE_H), 1)
    tally = 0;
    for c in deck:
        c_img = card_image(c[1])
        for i in range(0, c[0]):
            # Maybe coulda done this calc better, but...
            x = CARD_WIDTH * (tally % 3)
            y = CARD_HEIGHT * (math.floor(tally / 3) % 4)
            # print(x, y)
            # print(tally, math.floor(tally / 3) % 4, tally % 3)
            page.paste(c_img, (x, y))
            tally += 1
            if (tally % 12) == 0:
                pages.append(page.resize((1500, 2100)))
                page = Image.new('1', (PAGE_W, PAGE_H), 1)
    # pages[1].show()
    for p in pages:
        p.show()
    print(len(pages))

if __name__ == '__main__':
    main()        
