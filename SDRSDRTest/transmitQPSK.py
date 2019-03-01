#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Transmitqpsk
# Generated: Fri Mar  1 10:04:54 2019
##################################################


from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import iio
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import numpy


class transmitQPSK(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Transmitqpsk")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 6e6
        self.freq = freq = 2e6

        ##################################################
        # Blocks
        ##################################################
        self.pluto_sink_0 = iio.pluto_sink('ip:pluto.local', int(2400000000), int(samp_rate), int(freq), 0x8000, False, 10.0, '', True)
        self.digital_psk_mod_0 = digital.psk.psk_mod(
          constellation_points=4,
          mod_code="none",
          differential=True,
          samples_per_symbol=3,
          excess_bw=0.35,
          verbose=False,
          log=False,
          )
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, 'ARGUS/SDRSDRTest/transmitted.bin', False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.analog_random_source_x_0 = blocks.vector_source_b(map(int, numpy.random.randint(0, 256, 2500000)), False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_random_source_x_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.analog_random_source_x_0, 0), (self.digital_psk_mod_0, 0))
        self.connect((self.digital_psk_mod_0, 0), (self.pluto_sink_0, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.pluto_sink_0.set_params(int(2400000000), int(self.samp_rate), int(self.freq), 10.0, '', True)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.pluto_sink_0.set_params(int(2400000000), int(self.samp_rate), int(self.freq), 10.0, '', True)


def main(top_block_cls=transmitQPSK, options=None):

    tb = top_block_cls()
    tb.start()
    tb.wait()


if __name__ == '__main__':
    main()
