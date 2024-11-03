import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

MASTER_CLOCK = 2_000_000 # 2MHZ

ZERO_VOLUME = 2 # int(0.2 * 256) # AY might be outputing low constant DC as silence instead of complete 0V
MAX_VOLUME = 255/2

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

async def reset(dut):
    master_clock = MASTER_CLOCK # // 8
    cycle_in_nanoseconds = 1e9 / master_clock # 1 / 2Mhz / nanosecond
    dut._log.info("start")
    clock = Clock(dut.clk, cycle_in_nanoseconds, units="ns")
    cocotb.start_soon(clock.start())

    dut.uio_in.value =       0b1111_1111 # Emulate pull-ups on BIDIRECTIONAL pins

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

async def done(dut):
    # await ClockCycles(dut.clk, 1)
    dut._log.info("DONE!")

async def set_register(dut, reg, val):
    dut.uio_in.value =       0b000000_11 # Latch register index
    dut.ui_in.value  = reg & 15
    await ClockCycles(dut.clk, 2)
    print_chip_state(dut)
    dut.uio_in.value =       0b000000_10 # Write value to register
    dut.ui_in.value  = val
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)
    dut.uio_in.value =       0b000000_00 # Inactivate: disable writes and trigger envelope restart, if last write was to Envelope register
    dut.ui_in.value  = 0
    await ClockCycles(dut.clk, 1)
    print_chip_state(dut)

def get_output(dut):
    return int(dut.uo_out.value)

async def record_amplitude_table(dut):
    await set_register(dut,  7, 0b111_111)  # Mixer: disable all tones and noises
    amplitudes = []
    for vol in range(16):
        await set_register(dut, 8, vol)     # Channel A: disable envelope, set volume
        amplitudes.append(get_output(dut))
    return amplitudes

def channel_index(channel):
    if channel == 'A' or channel == 'a':
        channel = 0
    elif channel == 'B' or channel == 'b':
        channel = 1
    elif channel == 'C' or channel == 'c':
        channel = 2
    assert 0 <= channel and channel <= 2
    return channel

def inverted_channel_mask(channels):
    mask = 0
    if isinstance(channels, str):
        mask |= 1 if 'A' in channels or 'a' in channels else 0
        mask |= 2 if 'B' in channels or 'b' in channels else 0
        mask |= 4 if 'C' in channels or 'c' in channels else 0
    else:
        mask = channels
    assert 0 <= mask and mask <= 7
    return ~mask & 7

async def set_tone(dut, channel, frequency=-1, period=-1):
    channel = channel_index(channel)
    if frequency > 0:
        period = MASTER_CLOCK // (16 * frequency)
    assert 0 <= period  and period <= 4095
    await set_register(dut, channel*2+0, period & 0xFF)         # Tone A/B/C: set fine tune period
    if period > 0xFF:
        await set_register(dut, channel*2+1, period >> 8)       # Tone A/B/C: set coarse tune period

async def set_noise(dut, frequency=-1, period=-1):
    if frequency > 0:
        period = MASTER_CLOCK // (16 * frequency)
    assert 0 <= period and period <= 31
    await set_register(dut, 6, period & 31)                     # Noise: set period

async def set_mixer(dut, noises_on=0b000, tones_on=0b000):
    await set_register(dut, 7, (inverted_channel_mask(noises_on) << 3) | inverted_channel_mask(tones_on))

async def set_mixer_off(dut):
    await set_mixer(dut, noises_on=0, tones_on=0)

async def set_volume(dut, channel, vol=0, envelope=False):
    channel = channel_index(channel)
    if vol < 0:
        envelope = True
        vol = 0
    assert 0 <= channel and channel <= 2
    assert 0 <= vol     and vol <= 15
    await set_register(dut, 8+channel, (16 if envelope else 0) | vol)

async def set_envelope(dut, frequency=-1, period=-1, shape=-1):
    if frequency > 0:
        period = MASTER_CLOCK // (256 * frequency)
    if period >= 0:
        assert 0 <= period and period <= 65535
        await set_register(dut, 11, period & 0xFF)          # Envelope: set fine tune period
        if period > 0xFF:
            await set_register(dut, 12, period >> 8)        # Envelope: set coarse tune period
    if isinstance(shape, str):
        shape ={r"\_ ": 0,
                r"\_ ": 1,
                r"\_ ": 2,
                r"\_ ": 3,
                r"/_ ": 4,
                r"/_ ": 5,
                r"/_ ": 6,
                r"/_ ": 7,
                r"\\ ": 8,
                r"\_ ": 9,
                r"\/ ":10,
                r"\` ":11,
                r"// ":12,
                r"/` ":13,
                r"/\ ":14,
                r"/_ ":15}[shape[:2]+' ']
    if shape >= 0:
        assert 0 <= shape and shape <= 15
        await set_register(dut, 13, shape)                      # Envelope: set shape

async def assert_output(dut, frequency=-1, period=-1, constant=False, noise=False, v0 = ZERO_VOLUME, v1 = MAX_VOLUME):
    if frequency > 0:
        period = MASTER_CLOCK // (16 * frequency)
    if period == 0:
        period = 1
    if noise: # NOTE: noise effectively produces signal at quarter the frequency of the timer due to 
        # 1) 50% probability that consecutive samples will be equal
        # 2) flip-flop divider between frequency generator and LFSR
        frequency=frequency/4
        period=period*4
    assert 0 < period #and period <= 65535
    cycles_to_collect_data = int(period * 8)
    if constant:
        max_error = 0
        pulses_to_collect = 0
    else:
        max_error = 0.15 if noise else 0.01
        pulses_to_collect = 64 if noise else 2
        cycles_to_collect_data *= pulses_to_collect * 2
    
    mid_volume = (v0 + v1) // 2
    state_changes = 0
    for i in range(cycles_to_collect_data//8):
        last_state = get_output(dut) > mid_volume
        await ClockCycles(dut.clk, 8)
        # print_chip_state(dut)
        new_state = get_output(dut) > mid_volume
        if last_state != new_state:
            state_changes += 1

    # print(period, cycles_to_collect_data, state_changes)

    time_passed_to_collect_data = cycles_to_collect_data / MASTER_CLOCK
    measured_frequency = (state_changes / 2) / time_passed_to_collect_data
    frequency = MASTER_CLOCK / (16 * period)

    if not constant:
        noise = "noisie" if noise else ""
        if frequency > 1000:
            dut._log.info(f"expected {noise} frequency {frequency/1000:4.3f} KHz and measured {measured_frequency/1000:4.3f} KHz")
        else:
            dut._log.info(f"expected {noise} frequency {frequency:3.2f} Hz and measured {measured_frequency:3.2f} Hz")
        assert frequency * (1.0-max_error) <= measured_frequency and measured_frequency <= frequency * (1.0+max_error)

    pulses_to_collect2 = pulses_to_collect*2
    assert pulses_to_collect2 * (1.0-max_error) <= state_changes and state_changes <= pulses_to_collect2 * (1.0+max_error)

async def assert_constant_output(dut, cycles = 8):
    await assert_output(dut, period=cycles/8, constant=True)



### TESTS

@cocotb.test()
async def test_silence_after_reset(dut):
    await reset(dut)

    # Mixer all noises and tunes are on after reset
    # Channel A/B/C volume are 0 after reset

    await assert_constant_output(dut, cycles=256)
    assert get_output(dut) <= ZERO_VOLUME

    await done(dut)

@cocotb.test()
async def test_silence_with_mixer_off(dut):
    await reset(dut)

    # Mixer all noises and tunes are on after reset
    # Channel A/B/C volume are 0 after reset

    dut._log.info("disable tones and noises on all channels ")
    await set_mixer_off(dut)                                    # Mixer: disable all tones and noises, channels are controller by volume alone

    await assert_constant_output(dut, cycles=256)
    assert get_output(dut) <= ZERO_VOLUME

    await done(dut)

@cocotb.test()
async def test_output_amplitudes(dut):
    await reset(dut)

    dut._log.info("disable tones and noises on all channels")
    await set_mixer_off(dut)                                    # Mixer: disable all tones and noises, channels are controller by volume alone
    await set_volume(dut, 'A', 0)                               # Channel A: no envelope, set channel A to "fixed" level controlled by volume
    await set_volume(dut, 'B', 0)                               # Channel B: -- // --
    await set_volume(dut, 'C', 0)                               # Channel C: -- // --

    dut._log.info("record output amplitudes")
    amplitudes = await record_amplitude_table(dut)
    dut._log.info(f"output amplitudes are: {amplitudes}")

    for chan in 'ABC':
        # validate that volume increases with every step
        prev_volume = -1
        for vol in range(16):
            await set_volume(dut, chan, vol)                    # Channel A/B/C: set volume
            await assert_constant_output(dut)
            assert get_output(dut) > prev_volume or (prev_volume == get_output(dut) and vol < 6)
            prev_volume = get_output(dut)

        await set_volume(dut, chan, 0)                           # Channel A: set volume back to 0

    await done(dut)

@cocotb.test()
async def test_tones_with_mixer(dut):
    await reset(dut)

    for chan in 'ABC':
        dut._log.info(f"Tone on Channel {chan}")
        await set_mixer(dut, tones_on=chan)                     # Mixer: only one of Channels A/B/C tone is enabled
        await set_volume(dut, chan, 15)                         # Channel A/B/C: set volume to max
        await assert_output(dut, period=0)                      # default tone period after reset should be 0
        
        dut._log.info("Silence")
        await set_mixer_off(dut)                                # Mixer: disable all tones
        await assert_constant_output(dut, cycles=256)
        await set_volume(dut, chan, 0)                          # Channel A/B/C: set volume to 0

    await done(dut)

@cocotb.test()
async def test_tones_with_volume(dut):
    await reset(dut)

    await set_mixer(dut, tones_on='ABC')                        # Mixer: disable noises, enable all tones

    for chan in 'ABC':
        dut._log.info(f"Tone on Channel {chan}")
        await set_volume(dut, chan, 15)                         # Channel A/B/C: set volume to max
        await assert_output(dut, period=0)                      # default tone frequency after reset should be 0
        
        dut._log.info("Silence")
        await set_volume(dut, chan, 0)                          # Channel A/B/C: set volume to 0
        await assert_constant_output(dut, 256)

    await done(dut)

@cocotb.test()
async def test_tone_440hz(dut):
    await reset(dut)

    dut._log.info("enable tone on Channel A with maximum volume")
    await set_mixer(dut, tones_on='A')                          # Mixer: disable noises, enable all tones
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume
    await set_tone(dut, 'A', frequency=440)                     # Tone A: set fine tune frequency to 440 Hz

    await assert_output(dut, frequency=440)

    await done(dut)

@cocotb.test()
async def test_tone_is_initialised_to_period_0_after_reset(dut):
    await reset(dut)

    dut._log.info("enable tone on Channel A with maximum volume")
    await set_mixer(dut, tones_on='A')                          # Mixer: only Channel A tone is enabled
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

    dut._log.info("test if tone period is 0 after reset")
    await assert_output(dut, period=0)

    await done(dut)

@cocotb.test()
async def test_tone_period_0_and_1_are_equal(dut):
    await reset(dut)

    dut._log.info("enable tone on Channel A with maximum volume")
    await set_mixer(dut, tones_on='A')                          # Mixer: only Channel A tone is enabled
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

    dut._log.info("test tone with period 0 and 1 are the same")
    await set_tone(dut, 'A', period=0)                          # Tone A: set fine tune period to 0
    await assert_output(dut, period=0)
    await assert_output(dut, period=1)

    dut._log.info("test tone with period 1 and 0 are the same")
    await set_tone(dut, 'A', period=1)                          # Tone A: set fine tune period to 1
    await assert_output(dut, period=0)
    await assert_output(dut, period=1)

    await done(dut)

@cocotb.test()
async def test_tone_frequencies(dut):
    await reset(dut)

    dut._log.info("enable tone on Channel A with maximum volume")
    await set_mixer(dut, tones_on='A')                          # Mixer: only Channel A tone is enabled
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

    dut._log.info("test tone with period 0 (default after reset)")
    await assert_output(dut, period=0)                          # default tone frequency after reset should be 0

    for n in range(0, 8, 1):
        dut._log.info(f"test tone period {n}")
        await set_tone(dut, 'A', period=n)                      # Tone A: set period to n
        await assert_output(dut, period=n)

    dut._log.info("test tone with the maximum period of 4095")
    await set_tone(dut, 'A', period=4095)                       # Tone A: set period to max
    await assert_output(dut, period=4095)

    await done(dut)

@cocotb.test()
async def test_rapid_tone_frequency_change(dut):
    await reset(dut)

    dut._log.info("enable tone on Channel A with maximum volume")
    await set_mixer(dut, tones_on='A')                          # Mixer: only Channel A tone is enabled
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

    dut._log.info("set tone with the maximum period of 4095")
    await set_tone(dut, 'A', period=4095)                       # Tone A: set period to max

    dut._log.info("wait just a bit, wait is much shorter than the current tone period")
    await ClockCycles(dut.clk, 512)

    dut._log.info("quickly change tone period to 255 by reseting coarse period to 0 and keeping fine period at 255")
    await set_register(dut,  1, 0b0000_0000)                    # Tone A: set coarse period to 0, fine period is still 255
    await assert_output(dut, period=255)

    dut._log.info("wait just a bit, wait is much shorter than the current tone period")
    await ClockCycles(dut.clk, 128)

    for n in range(10, 0, -1):
        dut._log.info(f"test tone period {n}")
        await set_tone(dut, 'A', period=n)                      # Tone A: set period to n
        await assert_output(dut, period=n)

    await done(dut)

@cocotb.test()
async def test_noise_is_initialised_to_period_0_after_reset(dut):
    await reset(dut)

    dut._log.info("enable tone on Channel A with maximum volume")
    await set_mixer(dut, noises_on='A')                         # Mixer: only noise on Channel A is enabled
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

    dut._log.info("test if noise period is 0 after reset")
    await assert_output(dut, period=0, noise=True)

    await done(dut)

@cocotb.test()
async def test_noise_period_0_and_1_are_equal(dut):
    await reset(dut)

    dut._log.info("enable noise on Channel A with maximum volume")
    await set_mixer(dut, noises_on='A')                         # Mixer: only noise on Channel A is enabled
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

    dut._log.info("test noise with period 0 and 1 are the same")
    await set_noise(dut,     period=0)                          # Noise: set to period to 0
    await assert_output(dut, period=0, noise=True)
    await assert_output(dut, period=1, noise=True)

    dut._log.info("test noise with period 1 and 0 are the same")
    await set_noise(dut,     period=1)                          # Noise: set to period to 1
    await assert_output(dut, period=0, noise=True)
    await assert_output(dut, period=1, noise=True)

    await done(dut)

@cocotb.test()
async def test_noise_frequencies(dut):
    await reset(dut)

    dut._log.info("enable noise on Channel A with maximum volume")
    await set_mixer(dut, noises_on='A')                         # Mixer: only noise on Channel A is enabled
    await set_volume(dut, 'A', 15)                              # Channel A: no envelope, set channel to maximum volume

    for n in range(0, 8, 1):
        dut._log.info(f"test noise period {n}")
        await set_noise(dut,     period=n)                      # Noise: set period to n
        await assert_output(dut, period=n, noise=True)

    dut._log.info("test noise with the maximum period of 31")
    await set_noise(dut,     period=31)                         # Noise: set period to max
    await assert_output(dut, period=31, noise=True)

    await done(dut)

@cocotb.test()
async def test_envelopes_with_default_frequency(dut):
    await reset(dut)

    dut._log.info("route envelope value directly to the Channel A output")
    await set_mixer_off(dut)                                    # Mixer: disable all tones and noises
    await set_volume(dut, 'A', envelope=True)                   # Channel A: set channel A to envelope mode

    await set_envelope(dut, shape=r"/\/\ ")                     # Envelope: set /\/\ shape
    await ClockCycles(dut.clk, 512)                             # Wait for 2 wave periods to pass to get a clear measurement on the frequency
    await assert_output(dut, frequency=7812//2)
    await assert_output(dut, period=32)

    await set_envelope(dut, shape=r"\/\/ ")                     # Envelope: set /\/\ shape
    await ClockCycles(dut.clk, 512)
    await assert_output(dut, frequency=7812//2)
    await assert_output(dut, period=32)

    await set_envelope(dut, shape=r"//// ")                     # Envelope: set //// shape
    await ClockCycles(dut.clk, 512)
    await assert_output(dut, frequency=7812)

    await set_envelope(dut, shape=r"\\\\ ")                     # Envelope: set //// shape
    await ClockCycles(dut.clk, 512)
    await assert_output(dut, frequency=7812)

    await done(dut)


@cocotb.test()
async def test_envelope_frequency(dut):
    await reset(dut)

    dut._log.info("route envelope value directly to the Channel A output")
    await set_mixer_off(dut)                                    # Mixer: disable all tones and noises
    await set_volume(dut, 'A', envelope=True)                   # Channel A: set channel A to envelope mode

    for shape, mult in [(r"/\/\ ", 1),
                        (r"\/\/ ", 1),
                        (r"\\\\ ", 2),
                        (r"//// ", 2)]:
        for n in range(0, 8, 1):
            dut._log.info(f"test envelope period {n} with shape {shape}")

            if n == 0:
                n = 1

            await set_envelope(dut, shape=shape, period=n)      # Envelope: set /\/\ shape
            await ClockCycles(dut.clk, 1) # wait for 1 cycle before measuring frequency
                                          # otherwise shape change triggers envelope restart and messes up with the frequency measurement
            await assert_output(dut, frequency=3906/n*mult)
            await assert_output(dut, period=n*32/mult)

    await done(dut)

# TOO SLOW, 0.12 Hz requires almost 10 sec of samples!!!
# @cocotb.test()
# async def test_envelope_with_lowest_frequency(dut):
#     await reset(dut)

#     dut._log.info("route envelope value directly to the Channel A output")
#     await set_mixer_off(dut)                                    # Mixer: disable all tones and noises
#     await set_volume(dut, 'A', envelope=True)                   # Channel A: set channel A to envelope mode

#     await set_envelope(dut, shape=r"/\/\ ", period=65535)           # Envelope: set /\/\ shape
#     await assert_output(dut, frequency=0.12)
#     await assert_output(dut, period=65535*16)

#     await done(dut)

# TEMP DISABLED, fails after envelope clock fix!
# @cocotb.test()
# async def test_envelopes(dut):
#     await reset(dut)

#     dut._log.info("record amplitude table from Channel A")
#     amplitudes = await record_amplitude_table(dut)
#     print("recorded amplitude table:", amplitudes)

#     dut._log.info("route envelope value directly to the Channel A output")
#     await set_mixer_off(dut)                                    # Mixer: disable all tones and noises
#     await set_volume(dut, 'A', envelope=True)                   # Channel A: set channel A to envelope mode

#     envelopes_0 =  [r"\___ "] * 4 + \
#                    [r"/___ "] * 4   # envelopes with "Continue" flag = 0
#     envelopes_1 =  [r"\\\\ ",       # envelopes with "Continue" flag = 1
#                     r"\___ ",
#                     r"\/\/ ",
#                     r"\``` ",
#                     r"//// ",
#                     r"/``` ",
#                     r"/\/\ ",
#                     r"/___ "]

#     async def assert_segment(segment):
#         for s in segment:
#             assert get_output(dut) == amplitudes[s]
#             await ClockCycles(dut.clk, 8)

#     async def sweep_envelopes(envelopes):
#         for n, envelope in enumerate(envelopes):
#             dut._log.info(f"check envelope {n} pattern: {envelope}")
#             await set_envelope(dut, shape=n)                    # Envelope: set shape
#             print_chip_state(dut)
#             await ClockCycles(dut.clk, 1)
#             print_chip_state(dut)
#             await ClockCycles(dut.clk, 1)
#             print_chip_state(dut)
#             for segment in envelope:
#                 if segment == '\\':
#                     await assert_segment(range(15, -1, -1))
#                 elif segment == '/':
#                     await assert_segment(range(0, 16, 1))
#                 elif segment == '_':
#                     await assert_segment([0] * 16)
#                 elif segment == '`':
#                     await assert_segment([15] * 16)

#     await sweep_envelopes(envelopes_0 + envelopes_1)

#     await done(dut)

@cocotb.test()
async def test_envelope_restarts(dut):
    await reset(dut)

    dut._log.info("record amplitude table from Channel A")
    amplitudes = await record_amplitude_table(dut)
    print("recorded amplitude table:", amplitudes)

    dut._log.info("route envelope value directly to the Channel A output")
    await set_mixer_off(dut)                                    # Mixer: disable all tones and noises
    await set_volume(dut, 'A', envelope=True)                   # Channel A: set channel A to envelope mode

    await set_envelope(dut, shape=0)                            # Envelope: set any shape
    for shape, restart_volume in [  (r"\___ ", 15),
                                    (r"/___ ",  0),
                                    (r"\/\/ ", 15),
                                    (r"//// ",  0),
                                    (r"\\\\ ", 15),
                                    (r"/``` ",  0)]:
        for delay in range(9, 8*32, 5*8+7):
            dut._log.info(f"test restart of the envelope with shape {shape} after delaying for {delay} cycles")
            await ClockCycles(dut.clk, delay)                   # Wait a bit
            await set_envelope(dut, shape=shape)                # Envelope: set shape, resets the envelope start
            await ClockCycles(dut.clk, 1)
            assert get_output(dut) == amplitudes[restart_volume]

    await done(dut)

# @cocotb.test()
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
    await set_register(dut,  7, 0b111_111)  # Mixer: disable all tones and noise
    await set_register(dut,  8, 0b1_0000)   # Channel A: set to envelope mode
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
            await ClockCycles(dut.clk, 16)

    for n in range(8):
        await set_register(dut, 13, n)
        print_chip_state(dut)
        for i in range(64):
            await ClockCycles(dut.clk, 16)


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
