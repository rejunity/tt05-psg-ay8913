# How to run this script from command line:
#
# make MODULE=record VGM=../music/MISSION76496.bbc50hz.vgm MAX_TIME=10
#

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

import os
import numpy as np
from scipy.io.wavfile import write

# https://github.com/cdodd/vgmparse
# sudo pip install -e git+https://github.com/cdodd/vgmparse.git#egg=vgmparse
import vgmparse

VGM_FILENAME = "../music/MISSION76496.bbc50hz.vgm"
VGM_FILENAME = os.environ.get("VGM", VGM_FILENAME)
VGM_FILENAME = os.environ.get("VGM_FILENAME", VGM_FILENAME)

VERBOSE=False
try:
    VERBOSE = int(os.environ.get("VERBOSE", VERBOSE))
    if type(VERBOSE) == str:
        VERBOSE = VERBOSE.lower()
    if VERBOSE <= 0 or VERBOSE == "no" or VERBOSE == "false":
        VERBOSE = False
    elif VERBOSE >= 1 or VERBOSE == "yes" VERBOSE == "true":
        VERBOSE = True
except:
    pass

MAX_TIME = -1
try:
    MAX_TIME = int(os.environ.get("MAX_TIME", MAX_TIME))
except:
    pass

LOOP = 0
try:
    LOOP = int(os.environ.get("LOOP", LOOP))
except:
    pass

def print_chip_state(dut):
    if not VERBOSE:
        return

    try:
        internal = dut.tt_um_rejunity_ay8913_uut
        print(
            dut.ui_in.value, ">||"
            '{:2d}'.format(int(internal.latched_register.value)), 
            ("a" if internal.active   == 1 else ".") +
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
            '{:3d}'.format(int(dut.uo_out.value)))
                        # "@" if dut.uo_out[0].value == 1 else ".")
            # '{:3d}'.format(int(dut.uo_out.value >> 1)),
                        # "@" if dut.uo_out[0].value == 1 else ".")
    except:
        print(dut.uio_in.value, dut.ui_in.value, ">", dut.uo_out.value)

# TODO: def load_ym(filename, verbose=False):

def load_vgm(filename, verbose=False):
    # see https://vgmrips.net/wiki/VGM_Specification#Commands for command descriptions
    CHIP_NAME = 'AY-3-8910'
    CLOCK_METADATA = 'ay8910_clock'
    CMD_AY8910 = 0xA0
    CMD_WAIT_PERIOD = 0x61
    CMD_WAIT_60 = 0x62
    CMD_WAIT_50 = 0x63
    CMD_WAIT_0_15 = 0x70
    CMD_EOF = 0x66
    WAIT_PERIOD_60 = 735 # samples to wait at 60Hz with 44100 sampling rate
    WAIT_PERIOD_50 = 882 # samples to wait at 50Hz with 44100 sampling rate

    f = open(filename, mode="rb")
    data = f.read()
    f.close()
    vgm_data = vgmparse.Parser(data)
    print(vgm_data.metadata)

    clock_rate = vgm_data.metadata[CLOCK_METADATA]
    sampling_rate = 44100 # sampling rate is hardcoded in VGM
    seconds = vgm_data.metadata['total_samples'] / sampling_rate

    ay_commands = []
    for item in vgm_data.command_list:
        cmd = int.from_bytes(item['command'], 'little')
        if cmd == CMD_AY8910:
            addr = item['data'][0]
            data = item['data'][1]
            ay_commands.append([addr, data])
        elif cmd == CMD_WAIT_60:
            ay_commands.append([-1, WAIT_PERIOD_60])
        elif cmd == CMD_WAIT_50:
            ay_commands.append([-1, WAIT_PERIOD_50])
        elif CMD_WAIT_0_15 <= cmd and cmd <= CMD_WAIT_0_15 + 15:
            ay_commands.append([-1, cmd - CMD_WAIT_0_15 + 1])
        elif cmd == CMD_WAIT_PERIOD:
            wait = int.from_bytes(item['data'], 'little') if item['data'] != None else 0
            ay_commands.append([-1, wait])
        elif cmd == CMD_EOF:
            break
        else:
            raise AssertionError(f"Unsupported command 0x{cmd:02x} by {CHIP_NAME}")
    total_wait = sum([0 if c[0] >= 0 else c[1] for c in ay_commands])
    assert abs(total_wait - vgm_data.metadata['total_samples']) <= sampling_rate // 2

    return ay_commands, seconds, clock_rate, sampling_rate

@cocotb.test()
async def play_and_record_wav(dut):
    max_time = MAX_TIME
    vgm_filename = VGM_FILENAME

    music, length_in_seconds, clock_rate, sampling_rate = load_vgm(vgm_filename)

    if LOOP > 0:
        music = music * LOOP
        music_raw = music_raw * LOOP

    wave_file = [f"../output/{os.path.basename(vgm_filename).rstrip('.vgm')}.{ch}.wav" for ch in ["master", "channelA", "channelB", "channelC", "noise", "envelope"]]
    def get_sample(dut, channel):
            internal = dut.tt_um_rejunity_ay8913_uut
            if channel == 0:
                return int(dut.uo_out.value) << (15-8)    # 8-bit signal
            elif channel == 1:
                return int(internal.volume_A.value) << (15-8)      # 8-bit signal
            elif channel == 2:
                return int(internal.volume_B.value) << (15-8)      # 8-bit signal
            elif channel == 3:
                return int(internal.volume_C.value) << (15-8)      # 8-bit signal
            elif channel == 4:
                return int(internal.noise.value if \
                    internal.noise_disable_A.value +
                    internal.noise_disable_B.value +
                    internal.noise_disable_C.value < 3 else 0) << (15-1) # 1-bit signal
            elif channel == 5:
                return int(internal.envelope.value) << (15-4)      # 4-bit signal
            else:
                assert not "unknown channel"

    print(vgm_filename, "->", wave_file)
    print(f"VGM clock: {clock_rate}" )
    print(f"VGM length: {length_in_seconds:.2f} sec" )
    print(f"This script will record {max_time if max_time > 0 else length_in_seconds:.2f} sec" )
    
    master_clock = clock_rate // 8 # using chip configuration without clock divider for faster recording
    nanoseconds_per_cycle = 1e9 // master_clock
    nanoseconds_per_sample = 1e9 / sampling_rate

    await reset(dut, nanoseconds_per_cycle)
    print_chip_state(dut)

    last_time = 0
    samples = [[] for ch in wave_file]

    log_frame = []
    log_waited = 0
    for command in music:
        if command[0] >= 0:
            reg = command[0]
            data = command[1]
            await set_register(dut, reg, data)
            log_frame.append([reg, data])
        else:
            samples_to_wait = command[1]
            for i in range(samples_to_wait):
                await Timer(nanoseconds_per_sample, units="ns", round_mode="round")
                for channel, data in enumerate(samples):
                    sample = get_sample(dut, channel)
                    assert sample >= 0
                    assert sample <= 32767
                    if True:
                        sample *= 2
                        sample -= 32767
                        sample = -32767 if sample < -32767 else sample
                        sample =  32767 if sample > 32767 else sample
                    assert np.int16(sample) == sample
                    data.append(sample)
            log_waited += samples_to_wait

            cur_time = cocotb.utils.get_sim_time(units="ns")
            print(f"Recorded {len(samples[0])} samples. Wrote", [f"0x{ad[0]:1x}={ad[1]}" for ad in log_frame], f"and waited {(1000*log_waited)/44100:.2f} ms", "---", f"Time: {cur_time/1e6:5.3f} ms")
            log_frame = []
            log_waited = 0

            if cur_time > last_time + 1:
                for ch, data in enumerate(samples):
                    write(wave_file[ch], sampling_rate, np.int16(data))
                last_time = cur_time

            if max_time > 0 and max_time * 1e9 <= cur_time:
                break

    for ch, data in enumerate(samples):
        write(wave_file[ch], sampling_rate, np.int16(data))

    await done(dut)

async def reset(dut, nanoseconds_per_cycle):
    dut._log.info("start")
    clock = Clock(dut.clk, nanoseconds_per_cycle, units="ns")
    cocotb.start_soon(clock.start())

    dut.ui_in.value = 0 
    dut.uio_in.value = 0b000001_00 # Inactivate: disable writes and trigger envelope restart, if last write was to Envelope register

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

async def done(dut):
    await ClockCycles(dut.clk, 16)
    dut._log.info("DONE!")

async def set_register(dut, reg, val):
    dut.uio_in.value =       0b000001_11 # Latch register index
    dut.ui_in.value  = reg & 15
    await ClockCycles(dut.clk, 2)
    print_chip_state(dut)
    dut.uio_in.value =       0b000001_10 # Write value to register
    dut.ui_in.value  = val
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    dut.uio_in.value =       0b000001_00 # Inactivate: disable writes and trigger envelope restart, if last write was to Envelope register
    dut.ui_in.value  = 0
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
