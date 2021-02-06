
# XM-Sim Command File
# TOOL:	xmsim(64)	18.03-s001
#
#
# You can restore this configuration with:
#
#      xrun -timescale 1ns/1ns +incdir+src/inc -64bit -smartlib -smartorder -access +rwc -clean -lineclean +define+SIMULATION -defparam async_gp_fifo.SLOTS=16 -defparam async_gp_fifo.WIDTH=64 -input dump_all.tcl -licqueue -64 -xmlibdirpath sim_build -plinowarn -top async_gp_fifo -loadvpi /home/aignacio/.local/lib/python3.8/site-packages/cocotb/libs/libcocotbvpi_ius:vlog_startup_routines_bootstrap -access +rwc -createdebugdb src/inc/types_pkg.svh src/cdc_sync.sv src/async_gp_fifo.sv -input restore.tcl
#

set tcl_prompt1 {puts -nonewline "xcelium> "}
set tcl_prompt2 {puts -nonewline "> "}
set vlog_format %h
set vhdl_format %v
set real_precision 6
set display_unit auto
set time_unit module
set heap_garbage_size -200
set heap_garbage_time 0
set assert_report_level note
set assert_stop_level error
set autoscope yes
set assert_1164_warnings yes
set pack_assert_off {}
set severity_pack_assert_off {note warning}
set assert_output_stop_level failed
set tcl_debug_level 0
set relax_path_name 1
set vhdl_vcdmap XX01ZX01X
set intovf_severity_level ERROR
set probe_screen_format 0
set rangecnst_severity_level ERROR
set textio_severity_level ERROR
set vital_timing_checks_on 1
set vlog_code_show_force 0
set assert_count_attempts 1
set tcl_all64 false
set tcl_runerror_exit false
set assert_report_incompletes 0
set show_force 1
set force_reset_by_reinvoke 0
set tcl_relaxed_literal 0
set probe_exclude_patterns {}
set probe_packed_limit 4k
set probe_unpacked_limit 16k
set assert_internal_msg no
set svseed 1
set assert_reporting_mode 0
alias . run
alias quit exit
database -open -shm -into xcelium.shm xcelium.shm -default
probe -create -database xcelium.shm async_gp_fifo -all -variables -generics -dynamic -depth all -tasks -functions -uvm

simvision -input restore.tcl.svcf
