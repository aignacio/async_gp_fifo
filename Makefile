COCOTB_HDL_TIMEUNIT				= 1ns
COCOTB_HDL_TIMEPRECISION	= 1ns

VERILOG_SOURCES	:=	$(shell find . -type f -name *.svh)
VERILOG_SOURCES	+=	$(shell find . -type f -name *.v)
VERILOG_SOURCES	+=	$(shell find . -type f -name *.sv)

INCS_VERILOG		+=	src/inc
INCS_VERILOG		:=	$(addprefix +incdir+,$(INCS_VERILOG))

MACRO_VLOG			:=	SIMULATION
MACROS_VLOG			:=	$(addprefix +define+,$(MACRO_VLOG))
FIFO_SLOTS			:=	16
FIFO_WIDTH			:=	64
TEST_RUNS 			:=	20

MODULE					?= async_fifo_test
TOPLEVEL				?= async_gp_fifo
TOPLEVEL_LANG   ?= verilog
SIM							?= verilator
GUI							:= 0

export FIFO_SLOTS
export FIFO_WIDTH
export TEST_RUNS

ifeq ($(SIM),xcelium)
	EXTRA_ARGS	+=	$(INCS_VERILOG)	\
									-64bit					\
									-smartlib				\
									-smartorder			\
									-access +rwc		\
									-clean					\
									-lineclean			\
									$(MACROS_VLOG)	\
									-defparam async_gp_fifo.SLOTS=$(FIFO_SLOTS) \
									-defparam async_gp_fifo.WIDTH=$(FIFO_WIDTH) \
									-input dump_all.tcl
else ifeq ($(SIM),verilator)
	EXTRA_ARGS	+=	--trace-fst					\
									--trace-structs			\
									$(INCS_VERILOG)			\
									--report-unoptflat	\
									-GSLOTS=$(FIFO_SLOTS) \
									-GWIDTH=$(FIFO_WIDTH) \
									--Wno-UNOPTFLAT
else
$(error "Only sims suported now are Verilator/Xcelium/IUS")
endif

list:
	@echo "Listing all RTLs $(VERILOG_SOURCES)"
clean::
	@rm -rf sim_build waves.shm xrun.* xcelium.shm
err:
	@grep --color "*E" xrun.log
wv:
	/Applications/gtkwave.app/Contents/Resources/bin/gtkwave dump.fst

include $(shell cocotb-config --makefiles)/Makefile.sim
