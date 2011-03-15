#!/usr/bin/env python
# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# sinkelement.py
# (c) 2005 Edward Hervey <edward@fluendo.com>
# Licensed under LGPL
#
# Small test application to show how to write a sink element
# in 20 lines in python
#
# Run this script with GST_DEBUG=python:5 to see the debug
# messages

from ledwall import LedMatrix

import time
import pygst
pygst.require('0.10')
import gst
import gobject
import sys
gobject.threads_init ()

#
# Simple Sink element created entirely in python
#

class LedSink(gst.BaseSink):

    __gsttemplates__ = (
          gst.PadTemplate ("sink",
                            gst.PAD_SINK,
                            gst.PAD_ALWAYS,
                            gst.caps_from_string("video/x-raw-rgb,width=16,height=15,bpp=24,framerate=15/1")
                          ),
     )

    #_sinkpadtemplate = gst.PadTemplate ("sink",
    #                                    gst.PAD_SINK,
    #                                    gst.PAD_ALWAYS,
    #                                    gst.caps_from_string("video/x-raw-rgb,width=16,height=15,bpp=24")
#                                        gst.caps_new_any(),
    #                                    )
    sinkpad = property(lambda self: self.get_pad("sink"))

    def __init__(self, matrix):
        print("init")
        gst.BaseSink.__init__(self)
        self.matrix = matrix
        gst.info('creating sinkpad')
    #    self.sinkpad = gst.Pad(self._sinkpadtemplate, "sink")
        gst.info('adding sinkpad to self')
        #self.add_pad(self.sinkpad)
        self.set_sync(True)

        gst.info('setting chain/event functions')
        #self.sinkpad.set_chain_function(self.chainfunc)
        self.sinkpad.set_event_function(self.eventfunc)
        
    def chainfunc(self, pad, buffer):
        self.info("%s timestamp(buffer):%d len:%d" % (pad, buffer.timestamp, len(buffer)))
        self.buffer = buffer
        return gst.FLOW_OK

    def do_render(self, buffer):
        self.matrix.send_raw_image(buffer)
        return gst.FLOW_OK


    def eventfunc(self, pad, event):
        self.info("%s event:%r" % (pad, event.type))
        return True

gobject.type_register(LedSink)

class LedPipe:
  def __init__(self, location, matrix):
    # The pipeline
    self.pipeline = gst.Pipeline()
    self.pipeline.auto_clock()

    # Create bus and connect several handlers
    self.bus = self.pipeline.get_bus()
    self.bus.add_signal_watch()
    self.bus.connect('message::eos', self.on_eos)
    self.bus.connect('message::tag', self.on_tag)
    self.bus.connect('message::error', self.on_error)

    # Create elements
    self.src = gst.element_factory_make('filesrc')
    self.dec = gst.element_factory_make('decodebin')
    self.conv = gst.element_factory_make('autoconvert')
    #self.rsmpl = gst.element_factory_make('audioresample')
    self.color = gst.element_factory_make('ffmpegcolorspace')
    self.scale = gst.element_factory_make('videoscale')
    self.rate = gst.element_factory_make('videorate')
    self.audio = gst.element_factory_make('autoaudiosink')
    self.sink = LedSink(matrix) #gst.element_factory_make('alsasink')

    # Set 'location' property on filesrc
    self.src.set_property('location', location)

    # Connect handler for 'new-decoded-pad' signal 
    self.dec.connect('new-decoded-pad', self.on_new_decoded_pad)

    # Add elements to pipeline
    #self.pipeline.add(self.src, self.dec, self.conv, self.rsmpl, self.sink)
    self.pipeline.add(self.src, self.dec, self.conv, self.color, self.scale, self.rate, self.sink, self.audio)

    # Link *some* elements 
    # This is completed in self.on_new_decoded_pad()
    self.src.link(self.dec)
    #gst.element_link_many(self.conv, self.rsmpl, self.sink)
    gst.element_link_many(self.conv, self.scale, self.color, self.rate, self.sink)

    # Reference used in self.on_new_decoded_pad()
    self.vpad = self.conv.get_pad('sink')
    self.apad = self.audio.get_pad('sink')

    # The MainLoop
    self.mainloop = gobject.MainLoop()

    # And off we go!
    self.pipeline.set_state(gst.STATE_PLAYING)
    self.mainloop.run()


  def on_new_decoded_pad(self, element, pad, last):
    caps = pad.get_caps()
    name = caps[0].get_name()
    print 'on_new_decoded_pad:', name
    if name == 'video/x-raw-rgb':
      if not self.vpad.is_linked(): # Only link once
        pad.link(self.vpad)
    elif name == 'audio/x-raw-int':
      if not self.apad.is_linked(): # Only link once
        pad.link(self.apad)


	
  def on_eos(self, bus, msg):
    print 'on_eos'
    self.mainloop.quit()


  def on_tag(self, bus, msg):
    taglist = msg.parse_tag()
    print 'on_tag:'
    for key in taglist.keys():
      print '\t%s = %s' % (key, taglist[key])
	
	
  def on_error(self, bus, msg):
    error = msg.parse_error()
    print 'on_error:', error[1]
    self.mainloop.quit()
#
# class LedPipe:
#   def __init__(self, location, matrix):
#     # The pipeline
#     self.pipeline = gst.Pipeline()
#
#     # Create bus and connect several handlers
#     self.bus = self.pipeline.get_bus()
#     self.bus.add_signal_watch()
#     self.bus.connect('message::eos', self.on_eos)
#     self.bus.connect('message::tag', self.on_tag)
#     self.bus.connect('message::error', self.on_error)
#
#     # Create elements
#     self.src = gst.element_factory_make('filesrc')
#     self.dec = gst.element_factory_make('decodebin')
#     self.conv = gst.element_factory_make('autoconvert')
#     #self.rsmpl = gst.element_factory_make('audioresample')
#     self.color = gst.element_factory_make('ffmpegcolorspace')
#     self.scale = gst.element_factory_make('videoscale')
#     self.rate = gst.element_factory_make('videorate')
#     self.audio = gst.element_factory_make('autoaudiosink')
#     self.sink = LedSink(matrix) #gst.element_factory_make('alsasink')
#     self.player = gst.element_factory_make('playbin')
#     self.player.set_property("video-sink", self.sink)
#
#     # Set 'location' property on filesrc
#     self.src.set_property('location', location)
#     self.player.set_property('uri', "file://" + location)
#
#     # Connect handler for 'new-decoded-pad' signal 
#     self.dec.connect('new-decoded-pad', self.on_new_decoded_pad)
#
#     # Add elements to pipeline
#     #self.pipeline.add(self.src, self.dec, self.conv, self.rsmpl, self.sink)
#     #self.pipeline.add(self.src, self.dec, self.conv, self.color, self.scale, self.rate, self.sink, self.audio)
#     self.pipeline.add(self.player)
#
#     # Link *some* elements 
#     # This is completed in self.on_new_decoded_pad()
#     #self.src.link(self.player)
#     #gst.element_link_many(self.conv, self.rsmpl, self.sink)
#     #gst.element_link_many(self.player, self.scale, self.color, self.rate, self.sink)
#
#     # Reference used in self.on_new_decoded_pad()
#     self.vpad = self.conv.get_pad('sink')
#     self.apad = self.audio.get_pad('sink')
#
#     # The MainLoop
#     self.mainloop = gobject.MainLoop()
#
#     # And off we go!
#     self.pipeline.set_state(gst.STATE_PLAYING)
#     self.mainloop.run()
#
#
#   def on_new_decoded_pad(self, element, pad, last):
#     caps = pad.get_caps()
#     name = caps[0].get_name()
#     print 'on_new_decoded_pad:', name
#     if name == 'video/x-raw-rgb':
#       if not self.vpad.is_linked(): # Only link once
#         pad.link(self.vpad)
#     elif name == 'audio/x-raw-int':
#       if not self.apad.is_linked(): # Only link once
#         pad.link(self.apad)
#
#
# 	
#   def on_eos(self, bus, msg):
#     print 'on_eos'
#     self.mainloop.quit()
#
#
#   def on_tag(self, bus, msg):
#     taglist = msg.parse_tag()
#     print 'on_tag:'
#     for key in taglist.keys():
#       print '\t%s = %s' % (key, taglist[key])
# 	
# 	
#   def on_error(self, bus, msg):
#     error = msg.parse_error()
#     print 'on_error:', error[1]
#     self.mainloop.quit()
#

#
# Code to test the MySink class
#
matrix = LedMatrix()
LedPipe(sys.argv[1], matrix)
"""

src = gst.element_factory_make('filesrc')
src.set_property("location", "%s" %sys.argv[1])
gst.info('About to create LedSink')

#src = gst.element_factory_make('fakesrc')
sink = LedSink()
sink.set_property("name", "ledmatrix0")

#src = gst.element_factory_make('fakesrc')
converter = gst.element_factory_make('decodebin')
#aconverter = gst.element_factory_make('autoconvert')

pipeline = gst.Pipeline()
pipeline.add(src, converter, sink)


#pipeline.add(convert, 

src.link(converter)
converter.link(aconverter)
aconverter.link(sink)

pipeline.set_state(gst.STATE_PLAYING)

gobject.MainLoop().run()
"""