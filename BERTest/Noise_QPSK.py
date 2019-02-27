#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: NoiseQPSK
# Generated: Tue Feb 12 12:09:06 2019
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import numpy, sys, time

class Noise_QPSK(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "NoiseQPSK")
        global seed, initial_time, time2
        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 6e6
        self.gui_samprate = gui_samprate = 4e6

        ##################################################
        # Blocks
        ##################################################
        self.digital_psk_mod_0 = digital.psk.psk_mod(
          constellation_points=4,
          mod_code="none",
          differential=True,
          samples_per_symbol=3,
          excess_bw=0.35,
          verbose=False,
          log=False,
          )
        self.digital_psk_demod_0 = digital.psk.psk_demod(
          constellation_points=4,
          differential=True,
          samples_per_symbol=3,
          excess_bw=0.35,
          phase_bw=6.28/100.0,
          timing_bw=6.28/100.0,
          mod_code="none",
          verbose=False,
          log=False,
          )
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_char*1, samp_rate,True)
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_char*1, 'test2', False)
        self.blocks_file_sink_0_0.set_unbuffered(True)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, 'test1', False)
        self.blocks_file_sink_0.set_unbuffered(True)
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_random_source_x_0 = blocks.vector_source_b(map(int, numpy.random.randint(0, 2, 250000000)), False)
        time2 = time.time()
        print "Done with Sample Generation:", str(time2-initial_time), "seconds elapsed."
        
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, 0.05810575, int(seed))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.analog_random_source_x_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.digital_psk_demod_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.digital_psk_mod_0, 0))
        self.connect((self.digital_psk_demod_0, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.digital_psk_mod_0, 0), (self.blocks_add_xx_0, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)

    def get_gui_samprate(self):
        return self.gui_samprate

    def set_gui_samprate(self, gui_samprate):
        self.gui_samprate = gui_samprate


def main(top_block_cls=Noise_QPSK, options=None):
    global seed, initial_time, time2
    initial_time = time.time()
    tb = top_block_cls()
    tb.start()
    tb.wait()
    print "Done with program:", str(time.time()-time2), "seconds elapsed."


if __name__ == '__main__':
    global seed
    seed = sys.argv[1]
    main()
