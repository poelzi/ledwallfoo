#!/usr/bin/env python

import sys
import socket
import time

class LedMatrix:

    size = (16,15)

    def __init__(self, server="localhost", port=1338):
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server, port))

    def send_image(self, image):
        size = self.size
        sock = self.sock

        msg_format = "02" + "%02x" * 2 + "%02x" * 3 + "\r\n"

        for index, pixel in enumerate(image.getdata()):
            # 1-based index?
            x = index % size[0] + 1
            y = index / size[0] + 1

            sock.send(msg_format % ((x, y) + pixel))

class ColorFader:

    def __init__(self, colors, fade_steps=40):
        self.colors = colors
        self.fade_steps = fade_steps
        self.pos = (0, 0)

    def step(self):
        fade_steps = self.fade_steps
        pos = self.pos

        minor = (pos[1] + 1) % fade_steps

        if minor == 0:
            major = (pos[0] + 1) % len(self.colors)
        else:
            major = pos[0]

        self.pos = (major, minor)

    def color(self):
        return "#ff00ee"
        colors = self.colors
        pos = self.pos
        fade_steps = float(self.fade_steps)

        start = colors[pos[0]]
        target = colors[(pos[0] + 1) % len(colors)]

        color = tuple(a + (b - a) / fade_steps * pos[1] for a, b in zip(start, target))

        return ("#" + "%02x" * 3) % color


