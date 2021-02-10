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
import pytest
import cocotb_test.simulator

from cocotb.regression import TestFactory
from cocotb.clock import Clock
from cocotb.drivers import Driver
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer
from collections import namedtuple

CLK_100MHz = (10, "ns")
CLK_50MHz  = (20, "ns")
RST_CYCLES = 2
WAIT_CYCLES = 2

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
    dut._log.info("Configuring clocks... -- %d", clk_mode())
    print(clk_mode())
    if clk_mode() == 0:
        dut._log.info("50MHz - wr clk / 100MHz - rd clk")
        cocotb.fork(Clock(dut.wr_clk, *CLK_50MHz).start())
        cocotb.fork(Clock(dut.rd_clk, *CLK_100MHz).start())
    else:
        dut._log.info("50MHz - rd clk / 100MHz - wr clk")
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

def randomly_switch_config():
    return random.randint(0, 1)

async def run_test(dut, config_clock):
    MAX_SLOTS_FIFO = int(os.environ['PARAM_SLOTS'])
    MAX_WIDTH_FIFO = int(os.environ['PARAM_WIDTH'])
    TEST_RUNS = int(os.environ['TEST_RUNS'])
    await setup_dut(dut, config_clock)
    await reset_dut(dut)
    ff_driver = AFIFODriver(signals=dut)
    for i in range(TEST_RUNS):
        samples = [random.randint(0,(2**MAX_WIDTH_FIFO)-1) for i in range(random.randint(0,MAX_SLOTS_FIFO))]
        for i in samples:
            await ff_driver.write(i,exit_full=False)
        for i in samples:
            assert (read_value := await ff_driver.read(exit_empty=False)) == i, "%d != %d" % (read_value, i)

if cocotb.SIM_NAME:
    factory = TestFactory(run_test)
    factory.add_option('config_clock', [randomly_switch_config])
    factory.generate_tests()

#@pytest.mark.skipif(os.getenv("SIM") != "verilator", reason="Verilator is the only supported")
@pytest.mark.parametrize("slots",[2,4,8,16,32])
def test_async_fifo(slots):
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    rtl_dir   = tests_dir
    dut = "async_gp_fifo"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut
    verilog_sources = [
        os.path.join(rtl_dir, f"{dut}.sv"),
    ]
    parameters = {}
    parameters['SLOTS'] = slots
    parameters['WIDTH'] = 2**random.randint(2,10)

    extra_env = {f'PARAM_{k}': str(v) for k, v in parameters.items()}
    extra_env['TEST_RUNS'] = str(random.randint(2,20))
    extra_env['COCOTB_HDL_TIMEUNIT'] = "1ns"
    extra_env['COCOTB_HDL_TIMEPRECISION'] = "1ns"

    sim_build = os.path.join(tests_dir, "sim_build_pytest_simple_fifo_"+"_".join(("{}={}".format(*i) for i in parameters.items())))
    #extra_args =  ["-64bit                                          \
					  # -smartlib				                        \
					  # -smartorder			                            \
					  # -access +rwc		                            \
					  # -clean					                        \
					  # -lineclean			                            \
					  # -input ../dump_all.tcl"]

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
        extra_args=["--trace-fst","--trace-structs"]
        #extra_args=extra_args
    )
