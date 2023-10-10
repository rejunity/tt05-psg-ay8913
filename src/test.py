import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

def print_chip_state(dut):
    try:
        internal = dut.tt_um_rejunity_ay8913_uut
        print(
            '{:2d}'.format(int(internal.latched_register.value)), 
            ("A" if internal.active    == 1 else ".") +
            ("L" if internal.latch    == 1 else ".") +
            ("W" if internal.write    == 1 else ".") + "!",
            '{:4d}'.format(int(internal.tone_A_generator.period.value)),
            '{:4d}'.format(int(internal.tone_A_generator.counter.value)),
                        "|#|" if internal.tone_A_generator.out == 1 else "|-|", # "|",
            '{:4d}'.format(int(internal.tone_B_generator.period.value)),
            '{:4d}'.format(int(internal.tone_B_generator.counter.value)),
                        "|#|" if internal.tone_B_generator.out == 1 else "|-|", # "|",
            '{:4d}'.format(int(internal.tone_C_generator.period.value)),
            '{:4d}'.format(int(internal.tone_C_generator.counter.value)),
                        "|#|" if internal.tone_C_generator.out == 1 else "|-|",  #"!",
            '{:2d}'.format(int(internal.noise_generator.tone.period.value)),
            '{:2d}'.format(int(internal.noise_generator.tone.counter.value)),
                        ">" if internal.noise_generator.tone.out == 1 else " ",
            internal.noise_generator.lfsr.value,
                        "|#|" if internal.noise_generator.out == 1 else "|-|", # "|",
            '{:5d}'.format(int(internal.envelope_generator.tone.period.value)),
            '{:5d}'.format(int(internal.envelope_generator.tone.counter.value)),
            str(internal.register[13].value)[4:8],
                        ("A" if internal.envelope_generator.attack__    == 1 else ".") +
                        ("L" if internal.envelope_generator.alternate__ == 1 else ".") +
                        ("H" if internal.envelope_generator.hold__      == 1 else "."),
                        (">" if internal.restart_envelope               == 1 else "0"),
                        ("S" if internal.envelope_generator.stop        == 1 else "."),
            '{:1X}'.format(int(internal.envelope_generator.envelope_counter.value)),
                        "~" if internal.envelope_generator.invert_output == 1 else " ",
            '{:1X}'.format(int(internal.envelope_generator.out)),
                        ">>",
            '{:3d}'.format(int(dut.uo_out.value >> 1)),
                        "@" if dut.uo_out[0].value == 1 else ".")
    except:
        print(dut.uo_out.value)


async def set_register(dut, reg, val):
    dut.uio_in.value =       0b000000_11 # latch register
    dut.ui_in.value  = reg & 15
    await ClockCycles(dut.clk, 2)
    print_chip_state(dut)
    dut.uio_in.value =       0b000000_10 # write value
    dut.ui_in.value  = val
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    dut.uio_in.value =       0b000000_00 # inactivate
    dut.ui_in.value  = 0
    await ClockCycles(dut.clk, 1)

@cocotb.test()
async def test_psg(dut):

    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # print_chip_state(dut)

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    print_chip_state(dut)

    dut._log.info("init")
    await set_register(dut, 13, 0b0100)
    print_chip_state(dut)

    # // register[13] <= 4'b0000; //  \___
    # // register[13] <= 4'b0100; //  /___
    # // register[13] <= 4'b1000; //  \\\\
    # // register[13] <= 4'b1001; //  \___
    # // register[13] <= 4'b1010; //  \/\/
    # // register[13] <= 4'b1011; //  \```
    # // register[13] <= 4'b1100; //  ////
    # // register[13] <= 4'b1101; //  /```
    # // register[13] <= 4'b1110; //  /\/\
    # // register[13] <= 4'b1111; //  /___

    dut._log.info("run")
    for i in range(32):
        await ClockCycles(dut.clk, 16)
        print_chip_state(dut)

    dut._log.info("env")

    for n in range(8, 16):
        await set_register(dut, 13, n)
        print_chip_state(dut)
        for i in range(64):
            await ClockCycles(dut.clk, 16*16)

    for n in range(8):
        await set_register(dut, 13, n)
        print_chip_state(dut)
        for i in range(64):
            await ClockCycles(dut.clk, 16*16)


async def test_sn(dut):
    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    print_chip_state(dut)

    dut._log.info("init")
    for val in [
        # attenuation
        0b1_00_1_1110,  # channel 0
        0b1_01_1_1111,  # channel 1
        0b1_10_1_1111,  # channel 2
        0b1_11_1_1110,  # channel 3
        # frequency
        0b1_00_0_0001,  # tone 0
        0b1_01_0_0001,  # tone 1
        0b1_10_0_0001,  # tone 2
        # noise
        0b1_11_0_0111,  # noise 0
    ]:
        dut.ui_in.value = val
        await ClockCycles(dut.clk, 1)    
    print_chip_state(dut)

    dut._log.info("warmup 4 cycles")
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    
    dut._log.info("warmup 1018 cycles")
    await ClockCycles(dut.clk, 0x400-6)
    print_chip_state(dut)
    
    dut._log.info("warmup last 2 cycles")
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)

    dut._log.info("test freq 1")
    dut.ui_in.value = 0b1_00_0_0001     # tone 0 <- 1
    for i in range(8):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 1)

    dut._log.info("test freq 0")
    dut.ui_in.value = 0b1_00_0_0000     # tone 0 <- 0
    for i in range(16):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 1)

    dut._log.info("clock x64 speedup")
    for i in range(32):
        print_chip_state(dut)
        await ClockCycles(dut.clk, 64)

    dut._log.info("done")
