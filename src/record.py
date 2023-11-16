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
    try:
        internal = dut.tt_um_rejunity_ay8913_uut
        print(
            dut.ui_in.value, ">||"
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

    # # setup commands according to playback rate
    # if playback_rate == 50:
    #     CMD_WAIT = CMD_WAIT_50
    #     WAIT_PERIOD = WAIT_PERIOD_50
    # elif playback_rate == 60:
    #     CMD_WAIT = CMD_WAIT_60
    #     WAIT_PERIOD = WAIT_PERIOD_60
    # elif playback_rate > 0:
    #     CMD_WAIT = -1
    #     WAIT_PERIOD = 44100 // playback_rate

    # jagged = []
    # frame = []
    # total_wait = 0
    # for i, item in enumerate(vgm_data.command_list):
    #     cmd = int.from_bytes(item['command'], 'little')
    #     if (cmd == CMD_AY8910):
    #         addr = item['data'][0] if item['data'] != None else 0
    #         data = item['data'][1] if item['data'] != None else 0
    #         frame.append([addr, data])
    #     elif cmd == CMD_WAIT or cmd == CMD_WAIT_PERIOD or cmd == CMD_EOF:
    #         data = int.from_bytes(item['data'], 'little') if item['data'] != None else 0
    #         total_wait += (WAIT_PERIOD if cmd == CMD_WAIT else data)

    #         jagged.append(frame)
    #         frame = []

    #         if cmd == CMD_WAIT_PERIOD:
    #             assert data >= WAIT_PERIOD
    #             assert data % WAIT_PERIOD == 0
    #             for n in range(data // WAIT_PERIOD - 1):
    #                 jagged.append([])
    #     else:
    #         raise AssertionError(f"Unsupported command by {CHIP_NAME}")
    # assert frame == []
    # assert WAIT_PERIOD*(len(jagged)-1) >= total_wait or total_wait <= WAIT_PERIOD*len(jagged)
    # return jagged, playback_rate, clock_rate

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
                    internal.noise_disable_C.value < 3 else 0) << (15-1)         # 1-bit signal
            elif channel == 5:
                return int(internal.envelope.value) << (15-4)      # 4-bit signal
            else:
                assert not "unknown channel"

    print(vgm_filename, "->", wave_file)
    print(f"VGM clock: {clock_rate}" )
    print(f"VGM length: {length_in_seconds:.2f} sec" )
    print(f"This script will record {max_time if max_time > 0 else length_in_seconds:.2f} sec" )
    
    WRITE_DISABLED  = 0b1111_01_00 # SEL = 1 :: no clock div ; BDIR = 0, BC1 = 0 :: idle
    LATCH_REGISTER  = 0b1111_01_11 # SEL = 1 :: no clock div ; BDIR = 1, BC1 = 1 :: latch
    WRITE_DATA      = 0b1111_01_10 # SEL = 1 :: no clock div ; BDIR = 1, BC1 = 0 :: write

    master_clock = clock_rate // 8 # using chip configuration without clock divider for faster recording
    # fps = playback_rate
    # cycles_per_frame = master_clock / fps
    nanoseconds_per_cycle = 1e9 // master_clock
    nanoseconds_per_sample = 1e9 / sampling_rate
    # cycles_per_sample = nanoseconds_per_sample / nanoseconds_per_cycle
    # print("cycle in nanoseconds", nanoseconds_per_cycle, "cycles per frame:", cycles_per_frame, "cycles per wav sample", cycles_per_sample)
    # print("1 sec check:", fps * cycles_per_frame * nanoseconds_per_cycle / 1e9, "samples check", 1e9 / (cycles_per_sample * cycle_in_nanoseconds))


    await reset(dut, nanoseconds_per_cycle)
    print_chip_state(dut)

    last_time = 0
    samples = [[] for ch in wave_file]

    frame = []
    waited = 0
    for command in music:
        if command[0] >= 0:
            reg = command[0]
            data = command[1]
            await set_register(dut, reg, data)
            print_chip_state(dut)
            frame.append([reg, data])
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
            waited += samples_to_wait

            cur_time = cocotb.utils.get_sim_time(units="ns")
            print(f"Recorded {len(samples[0])} samples. Wrote", [f"0x{ad[0]:1x}={ad[1]}" for ad in frame], f"and waited {(1000*waited)/44100:.2f} ms", "---", f"Time: {cur_time/1e6:5.3f} ms")
            frame = []
            waited = 0

            if cur_time > last_time + 1:
                for ch, data in enumerate(samples):
                    write(wave_file[ch], sampling_rate, np.int16(data))
                last_time = cur_time

            if max_time > 0 and max_time * 1e9 <= cur_time:
                break

    # for frame in music:
    #     cur_time = cocotb.utils.get_sim_time(units="ns")
    #     if max_time > 0 and max_time * 1e9 <= cur_time:
    #         for ch, data in enumerate(samples):
    #             write(wave_file[ch], sampling_rate, np.int16(data))
    #         break

    #     if len(frame) > 0:
    #         print("---", n, len(samples[0]), "---", [f"{ad[0]}:{ad[1]}" for ad in frame], "---", "time in ms:", format(cur_time/1e6, "5.3f"),)
    #     for ad in frame:
    #         set_register(dut, ad[0], ad[1])
    #     #     dut.ui_in.value = ad[0]
    #     #     dut.uio_in.value = LATCH_REGISTER
    #     #     await ClockCycles(dut.clk, 1)
    #     #     dut.ui_in.value = ad[1]
    #     #     dut.uio_in.value = WRITE_DATA
    #     #     await ClockCycles(dut.clk, 1)
    #     #     print_chip_state(dut)
    #     # dut.uio_in.value = WRITE_DISABLED

    #     while cocotb.utils.get_sim_time(units="ns") < cur_time + (1e9 / fps):
    #         await Timer(nanoseconds_per_sample, units="ns", round_mode="round")
    #         for channel, data in enumerate(samples):
    #             sample = get_sample(dut, channel)
    #             assert sample >= 0
    #             assert sample <= 32767
    #             if True:
    #                 sample *= 2
    #                 sample -= 32767
    #                 sample = -32767 if sample < -32767 else sample
    #                 sample =  32767 if sample > 32767 else sample
    #             assert np.int16(sample) == sample
    #             data.append(sample)

    #     print_chip_state(dut)

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
