#!/usr/bin/python

# pip imports
from mtgsdk import Card
from mtgsdk import Set
from PIL import Image, ImageDraw, ImageFont
# stdlib imports
import argparse, sys, math, re

# Globals for Scale (in future, add num per page?)
# Page Card: 500 x 700
FONT_SIZE = 14
FONT ='/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf'
CARD_W = 500 # * 2
CARD_H = 700 # * 2
# I want to reword card scaling eventually... right now, they
# act as calculations for the x/y coords to place text, but
# there's gotta be better ways to calc this lol
EDGE_SCALE = CARD_W / 60 
N_SCALE = CARD_H / 20
T_SCALE = CARD_H / 2.2
O_SCALE = CARD_H / 1.9 
# # of cards per page
NUM_P_W = 4
NUM_P_H = 4
# Dimensions of x * y cards that'll be on a page
PAGE_W = CARD_W * NUM_P_W
PAGE_H = CARD_H * NUM_P_H
# the final pixel count of a given page
PRINT_W = 563 * 2
PRINT_H = 750 * 2
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
def text_scalar(text, font, img_size, img_fill = 0.90):
    jump_size = 2;
    font_size = 1
    overflow = img_fill * img_size
    while True:
        if font.getsize(text)[0] < overflow:
            font_size += jump_size
        else:
            jump_size = jump_size // 2
            font_size -= jump_size
        font = ImageFont.truetype(FONT, font_size)
        if jump_size <= 1:
            if font_size > CARD_W / 11: # may be bad~44
                font_size = CARD_W // 11 
            return font_size

def add_name(d, card, font):
    cost = card.mana_cost
    if cost is None:
        cost = ''
    top = card.name + '    ' + cost
    n_size = text_scalar(top, font, CARD_W)
    d.text((EDGE_SCALE, N_SCALE), top, fill='black', anchor='ls', 
        font=ImageFont.truetype(FONT, n_size))
    return d

def add_type(d, card, font):
    t_size = text_scalar(card.type, font, CARD_W)
    d.text((EDGE_SCALE, T_SCALE), card.type, fill='black', anchor='ls',
        font=ImageFont.truetype(FONT, t_size))
    return d

def add_text(d, card, font):
    # 11 words max?
    text = card.text.splitlines()
    row = O_SCALE
    queue = []
    size = 999; # default
    for par in text:
        body = par.split()
        n_per_line = 6 if len(body) > 45 else 5
        while len(body) > 0:
            clip = min(len(body), n_per_line) 
            sub = ' '.join(body[0:clip])
            new_size = text_scalar(sub, font, CARD_W)
            size = min(new_size, size)
            queue.append(sub)
            body = body[clip:]
        queue.append('#BUFFER#')
    for l in queue:
        if l == '#BUFFER#':
            row += size
            continue
        d.text((EDGE_SCALE, row), l, fill='black', anchor='ls',
            font=ImageFont.truetype(FONT, size))
        row += size
    return d

def add_br_text(d, card, font):
    if not card.power and not card.loyalty:
        return
    text = ''
    size = text_scalar(card.name, font, CARD_W) - \
        text_scalar(card.text, font, CARD_W)
    if card.loyalty:
        text = '{' + card.loyalty + '}'
    if card.power:
        text = card.power + '/' + card.toughness
    print(text)
    x = int(CARD_W - EDGE_SCALE - size)
    y = int(CARD_H - EDGE_SCALE - size)
    print(x, y)
    d.text((x, y), text, fill='black', anchor = 'rs',
        font=ImageFont.truetype(FONT, size))
    # d.text((CARD_W - EDGE_SCALE, CARD_H - EDGE_SCALE), text,
    #     fill='black', anchor='ls', font=FONT)

def card_image(card):
    print('#', end='')
    font = ImageFont.truetype(FONT, 1)
    cd = Image.new('1', (CARD_W, CARD_H), 1) # 1=BW
    d = ImageDraw.Draw(cd)
    d = add_name(d, card, font)
    d = add_type(d, card, font)
    d = add_text(d, card, font)
    d = add_br_text(d, card, font)
    return cd

def cut_lines(page):
    pg = ImageDraw.Draw(page)
    for i in range(1, NUM_P_W):
        x = (i * CARD_W) - EDGE_SCALE
        pg.line([(x, 0), (x, PAGE_H)], fill='black', width=2)
    for j in range(1, NUM_P_H):
        y = (j * CARD_H) - EDGE_SCALE
        pg.line([(0, y), (PAGE_W, y)], fill='black', width=2)
    return page

def main():
    deck = read_infile()
    # test = card_image(deck[0][1])
    pages = []
    page = Image.new('1', (PAGE_W, PAGE_H), 1)
    tally = 0;
    print('Drawing PDF...')
    print('[', end='')
    for c in deck:
        c_img = card_image(c[1])
        for i in range(0, c[0]):
            x = CARD_W * (tally % NUM_P_W)
            y = CARD_H * (math.floor(tally / NUM_P_W) % NUM_P_H)
            page.paste(c_img, (x, y))
            tally += 1
            if (tally % int(NUM_P_W * NUM_P_H)) == 0:
                pages.append(cut_lines(page).resize((PRINT_W, 
                    PRINT_H)))
                page = Image.new('1', (PAGE_W, PAGE_H), 1)
    # pages[1].show()
    if tally % int(NUM_P_W * NUM_P_H) != 0:
        pages.append(cut_lines(page).resize((PRINT_W, PRINT_H)))
    print(']')
    outfile = re.sub('[^.]+$', '', args.infile.name)[:-1] + '-printable.pdf'
    print('Done! File saved to', outfile)
    pages[0].save(outfile, save_all=True, append_images=pages[1:])

if __name__ == '__main__':
    main()        
