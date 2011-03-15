#!/usr/bin/python
from ledwall import LedMatrix, ColorFader

import sys
import time
import Image
import ImageDraw
import ImageFont

matrix = LedMatrix()

im = Image.new(mode="RGB", size=matrix.size)
clean_data = list(im.getdata())

draw = ImageDraw.Draw(im)

font = ImageFont.truetype("DejaVuSans.ttf", matrix.size[1])
draw.setfont(font)

text = "<<</>>" if len(sys.argv) < 2 else sys.argv[1]

image_width = matrix.size[0]
text_width = draw.textsize(text)[0]

width = text_width + image_width

step = 0

colors = [(0xff, 0x00, 0x00), (0x00, 0xff, 0x00), (0x00, 0x00, 0xff)]
fader = ColorFader(colors)

while True:
    draw.text((image_width - step, 0), text, fill=fader.color())
    matrix.send_image(im)

    step = (step + 1) % width

    fader.step()

    im.putdata(clean_data)
    time.sleep(0.2)

