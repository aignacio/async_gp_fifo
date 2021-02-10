#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 04.02.2021
# Last Modified Date: 04.02.2021
# Last Modified By  : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
import random
import cocotb
import os
import logging

from cocotb.clock import Clock
from cocotb.drivers import Driver
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer
from collections import namedtuple

CLK_100MHz = (10, "ns")
CLK_50MHz  = (20, "ns")
RST_CYCLES = 2
WAIT_CYCLES = 2
MAX_SLOTS_FIFO = int(os.environ['PARAM_SLOTS'])
MAX_WIDTH_FIFO = int(os.environ['PARAM_WIDTH'])
TEST_RUNS = int(os.environ['TEST_RUNS'])

class AFIFODriver(Driver):
    def __init__(self, signals, debug=False):
        level = logging.DEBUG if debug else logging.WARNING
        self.clk_wr   = signals.wr_clk
        self.valid_wr = signals.wr_en
        self.data_wr  = signals.wr_data
        self.ready_wr = signals.wr_full

        self.clk_rd   = signals.rd_clk
        self.valid_rd = signals.rd_empty
        self.data_rd  = signals.rd_data
        self.ready_rd = signals.rd_en

        self.valid_wr <= 0
        self.ready_rd <= 0
        Driver.__init__(self)
        self.log.setLevel(level)

    async def write(self, data, sync=True, **kwargs):
        self.log.info("WRITE AFIFO => %x"%data)
        while True:
            await FallingEdge(self.clk_wr)
            self.valid_wr <= 1
            self.data_wr  <= data
            await RisingEdge(self.clk_wr)
            if self.ready_wr == 0:
                break
            elif kwargs["exit_full"] == True:
                return 1
        self.valid_wr <= 0
        return 0

    async def read(self, sync=True, **kwargs):
        while True:
            await FallingEdge(self.clk_rd)
            if self.valid_rd == 0:
                data = self.data_rd.value # We capture before we incr. rd ptr
                self.ready_rd <= 1
                await RisingEdge(self.clk_rd)
                break
            elif kwargs["exit_empty"] == True:
                return "empty"
        self.log.info("READ AFIFO => %x"%data)
        self.ready_rd <= 0
        return data

async def setup_dut(dut, clk_mode):
    dut._log.info("Configuring clocks...")
    if clk_mode == 0:
        cocotb.fork(Clock(dut.wr_clk, *CLK_50MHz).start())
        cocotb.fork(Clock(dut.rd_clk, *CLK_100MHz).start())
    else:
        cocotb.fork(Clock(dut.rd_clk, *CLK_50MHz).start())
        cocotb.fork(Clock(dut.wr_clk, *CLK_100MHz).start())

async def reset_dut(dut):
    dut.wr_arst.setimmediatevalue(0)
    dut.rd_arst.setimmediatevalue(0)
    dut._log.info("Reseting DUT")
    dut.wr_arst <= 1
    dut.rd_arst <= 0
    await ClockCycles(dut.wr_clk, RST_CYCLES)
    dut.wr_arst <= 0
    dut.rd_arst <= 1
    await ClockCycles(dut.rd_clk, RST_CYCLES)
    dut.rd_arst <= 0

@cocotb.test()
async def afifo_basic_test(dut):
    """ Simple test to produce and consume data from the async fifo """
    await setup_dut(dut, 0)
    await reset_dut(dut)
    ff_driver = AFIFODriver(signals=dut)
    for i in range(TEST_RUNS):
        #await reset_dut(dut)
        samples = [random.randint(0,(2**MAX_WIDTH_FIFO)-1) for i in range(random.randint(0,MAX_SLOTS_FIFO))]
        for i in samples:
            await ff_driver.write(i,exit_full=False)
        for i in samples:
            assert (read_value := await ff_driver.read(exit_empty=False)) == i, "%x != %x" % (read_value, i)

@cocotb.test()
async def afifo_basic_inv_test(dut):
    """ Simple test inv, same thing just inverted clocks """
    await setup_dut(dut, 1)
    await reset_dut(dut)
    ff_driver = AFIFODriver(signals=dut)
    for i in range(TEST_RUNS):
        #await reset_dut(dut)
        samples = [random.randint(0,(2**MAX_WIDTH_FIFO)-1) for i in range(random.randint(0,MAX_SLOTS_FIFO))]
        for i in samples:
            await ff_driver.write(i,exit_full=False)
        for i in samples:
            assert (read_value := await ff_driver.read(exit_empty=False)) == i, "%d != %d" % (read_value, i)

@cocotb.test()
async def afifo_write_full(dut):
    """ Try to write even with fifo full """
    await setup_dut(dut, 1)
    await reset_dut(dut)
    ff_driver = AFIFODriver(signals=dut,debug=True)
    samples = [random.randint(0,(2**MAX_WIDTH_FIFO)-1) for i in range(MAX_SLOTS_FIFO)]
    for i in samples:
        assert ((feedback := await ff_driver.write(i,exit_full=False)) == 0), "AFIFO signaling FULL, where actually it's not!"
    assert ((feedback := await ff_driver.write(random.randint(0,(2**MAX_WIDTH_FIFO)-1),exit_full=True)) == 1), "AFIFO not signaling FULL correctly ==> dut.wr_full = %d" % dut.wr_full

@cocotb.test()
async def afifo_read_empty(dut):
    """ Try to read even with fifo empty """
    await setup_dut(dut, 1)
    await reset_dut(dut)
    ff_driver = AFIFODriver(signals=dut,debug=True)
    assert ((feedback := await ff_driver.read(exit_empty=True)) == "empty"), "AFIFO not signaling empty correctly ==> dut.rd_empty = %d" % dut.rd_empty
