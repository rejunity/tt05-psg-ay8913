/* verilator lint_off WIDTH */
`default_nettype none

// NOTE: The original AY-3-819x used (see lvd reverse engineering effort):
// 1) single input clock, but internally two phase clock generated by inverting the input clock,
// 2) asyncronous reset for clearing flip-flops to 0.
//
// However this implementation uses syncronous reset and single edge of the clock.

module tt_um_rejunity_ay8913 #( parameter DA7_DA4_UPPER_ADDRESS_MASK = 4'b0000,
                                parameter CHANNEL_OUTPUT_BITS = 9,
                                parameter MASTER_OUTPUT_BITS = 8
) (
    input  wire [7:0] ui_in,    // Dedicated inputs - connected to the input switches
    output wire [7:0] uo_out,   // Dedicated outputs - connected to the 7 segment display
    input  wire [7:0] uio_in,   // IOs: Bidirectional Input path
    output wire [7:0] uio_out,  // IOs: Bidirectional Output path
    output wire [7:0] uio_oe,   // IOs: Bidirectional Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    assign uio_oe[7:0] = 8'b1111_00_00; // the first 4 pins of the Bidirectional path are used for
                                        // bus control lines (BDIR and BC1) are set to input mode (=0),
                                        // clock divider pins (SEL0, SEL1)  are set to input mode (=0),
                                        // the rest of the pins are set to output mode (=1)
    assign uio_out[3:0] =      4'b0000; // the upper 4 pins: 3 channels PWM and master AUDIO_OUT in PWM mode
    wire reset = ! rst_n;

    wire [1:0] master_clock_control = uio_in[3:2];
    wire [7:0] data = ui_in;

    reg [$clog2(128)-1:0] clk_counter;
    reg clk_master_strobe;
    always @(*) begin
        case(master_clock_control[1:0])
            2'b01:  clk_master_strobe = 1;                                  // no div, counters for tone & noise are always enabled
                                                                            // useful to speedup record.py
            2'b10:  clk_master_strobe = clk_counter[$clog2(128)-1:0] == 0;  // div 128, for TinyTapeout5 running 32..50Mhz
            default:
                    clk_master_strobe = clk_counter[$clog2(8)-1:0] == 0;    // div  8, for standard AY-3-819x 
                                                                            // running on 1.7 MHz .. 2 MHz frequencies
        endcase
    end

    // AY-3-819x Bus Control Decode
    // NOTE: AY-3-819x to match design of CP1610 CPU has one more bus control line BC2
    // however in AY-3-8193 BC2 is left internal and is always pulled high to simplify the bus control logic.
    // BDIR  BC1
    //   0    0    Inactive
    //   0    1    Read from Register Array  (NOT IMPLEMENTED!)
    //   1    0    Write to Register Array
    //   1    1    Latch Register Address
    wire bdir = uio_in[1];
    wire bc1 = uio_in[0];
    wire bus_inactive   = !bdir && !bc1;
    wire bus_read       = !bdir &&  bc1;
    wire bus_write      =  bdir && !bc1;
    wire bus_latch_reg  =  bdir &&  bc1;

    // NOT IMPLEMENTED! A8 and A9 address lines
    wire cs = (data[7:4] == DA7_DA4_UPPER_ADDRESS_MASK);
    wire latch = bus_latch_reg && cs;
    wire write = bus_write && active;   // NOTE: chip must be in active state
                                        // in order to accept writes to the register file 

    localparam REGISTERS = 16;
    reg [3:0] latched_register;
    reg [7:0] register[REGISTERS-1:0];  // 82 bits are used out of 128
    reg active;                         // chip becomes active during the Latch Register Address phase
                                        // IFF cs==1 ({A9,A8,DA7..DA4} matches the chip mask)
    reg restart_envelope;

    always @(posedge clk) begin
        if (reset) begin
            clk_counter <= 0;
            latched_register <= 0;
            for (integer i = 0; i < REGISTERS; i = i + 1)
                register[i] <= 0;
            active <= 0;
            restart_envelope <= 0;
        end else begin
            clk_counter <= clk_counter + 1;                 // provides clk_master_strobe for tone, noise and envelope

            if (bus_latch_reg)                              // chip becomes active for subsequent reads/writes
                active <= cs;                               // IFF cs==1, during the Latch Register Address phase
                                                            // otherwise future data reads/writes will be ignored

            if (latch)
                latched_register <= data[3:0];
            else if (write)
                register[latched_register] <= data;

            restart_envelope <= write &&                    // restart envelope, if data is written
                                latched_register == 4'd13;  // to R13 Envelope Shape register
                                // NOTE: restart_envelope is held as long as the write cycle,
                                // which is accurate to the real AY-3-819x
        end
    end

    // AY-3-819x Register Array
    //     7 6 5 4 3 2 1 0
    // R0  x x x x x x x x Channel A Tone Period, Fine Tune
    // R1          x x x x                        Coarse Tune
    // R2  x x x x x x x x Channel B Tone Period, Fine Tune
    // R3          x x x x                        Coarse Tune
    // R4  x x x x x x x x Channel C Tone Period, Fine Tune
    // R5          x x x x                        Coarse Tune
    // R6        x x x x x Noise Period
    // R7      x x x x x x Mixer (signals inverted): Noise /C, /B, /A; Tone /C, /B, /A
    // R8        x x x x x Channel A Amplitude
    // R9        x x x x x Channel B Amplitude
    // R10       x x x x x Channel C Amplitude
    // R11 x x x x x x x x Envelop Period, Fine Tune
    // R12 x x x x x x x x                 Coarse Tune
    // R13         x x x x Envelope Shape / Cycle

    wire [11:0]  tone_period_A, tone_period_B, tone_period_C;
    wire [4:0]   noise_period;
    wire         tone_disable_A, tone_disable_B, tone_disable_C;
    wire         noise_disable_A, noise_disable_B, noise_disable_C;
    wire         envelope_A, envelope_B, envelope_C;
    wire [3:0]   amplitude_A, amplitude_B, amplitude_C;
    wire [15:0]  envelope_period;
    wire         envelope_continue, envelope_attack, envelope_alternate, envelope_hold;

    assign tone_period_A[11:0] = {register[1][3:0], register[0][7:0]};
    assign tone_period_B[11:0] = {register[3][3:0], register[2][7:0]};
    assign tone_period_C[11:0] = {register[5][3:0], register[4][7:0]};
    assign noise_period[4:0]   = register[6][4:0];
    assign {noise_disable_C,
            noise_disable_B,
            noise_disable_A,
            tone_disable_C,
            tone_disable_B,
            tone_disable_A} = register[7][5:0];
    assign {envelope_A, amplitude_A[3:0]} = register[ 8][4:0];
    assign {envelope_B, amplitude_B[3:0]} = register[ 9][4:0];
    assign {envelope_C, amplitude_C[3:0]} = register[10][4:0];
    assign envelope_period[15:0] = {register[12][7:0], register[11][7:0]};
    assign {envelope_continue,
            envelope_attack,
            envelope_alternate,
            envelope_hold} = register[13][3:0];


    // Tone, noise & envelope generators
    wire tone_A, tone_B, tone_C, noise;
    tone #(.PERIOD_BITS(12)) tone_A_generator (
        .clk(clk),
        .enable(clk_master_strobe),
        .reset(reset),
        .period(tone_period_A),
        .out(tone_A)
        );
    tone #(.PERIOD_BITS(12)) tone_B_generator (
        .clk(clk),
        .enable(clk_master_strobe),
        .reset(reset),
        .period(tone_period_B),
        .out(tone_B)
        );
    tone #(.PERIOD_BITS(12)) tone_C_generator (
        .clk(clk),
        .enable(clk_master_strobe),
        .reset(reset),
        .period(tone_period_C),
        .out(tone_C)
        );

    noise #(.PERIOD_BITS(5)) noise_generator (
        .clk(clk),
        .enable(clk_master_strobe),
        .reset(reset),
        .period(noise_period),
        .out(noise)
        );

    wire [3:0] envelope; // NOTE: Y2149 envelope outputs 5 bits, but programmable amplitude is only 4 bits!
    envelope #(.PERIOD_BITS(16), .ENVELOPE_BITS(4)) envelope_generator (
        .clk(clk),
        .enable(clk_master_strobe),
        .reset(reset | restart_envelope),
        .continue_(envelope_continue),
        .attack(envelope_attack),
        .alternate(envelope_alternate),
        .hold(envelope_hold),
        .period(envelope_period),
        .out(envelope)
        );

    // FROM https://github.com/mamedev/mame/blob/master/src/devices/sound/ay8910.cpp ay8910_device::sound_stream_update
    // The 8910 has three outputs, each output is the mix of one of the three
    // tone generators and of the (single) noise generator. The two are mixed
    // BEFORE going into the DAC. The formula to mix each channel is:
    // (ToneOn | ToneDisable) & (NoiseOn | NoiseDisable).
    // Note that this means that if both tone and noise are disabled, the output
    // is 1, not 0, and can be modulated changing the volume.
    wire channel_A = (tone_disable_A | tone_A) & (noise_disable_A | noise);
    wire channel_B = (tone_disable_B | tone_B) & (noise_disable_B | noise);
    wire channel_C = (tone_disable_C | tone_C) & (noise_disable_C | noise);

    wire [CHANNEL_OUTPUT_BITS-1:0] volume_A, volume_B, volume_C;
    attenuation #(.VOLUME_BITS(CHANNEL_OUTPUT_BITS)) attenuation_A ( // @TODO: rename to amplitude to match docs
        .in(channel_A),
        .control(envelope_A ? envelope: amplitude_A),
        .out(volume_A)
        );
    attenuation #(.VOLUME_BITS(CHANNEL_OUTPUT_BITS)) attenuation_B (
        .in(channel_B),
        .control(envelope_B ? envelope: amplitude_B),
        .out(volume_B)
        );
    attenuation #(.VOLUME_BITS(CHANNEL_OUTPUT_BITS)) attenuation_C (
        .in(channel_C),
        .control(envelope_C ? envelope: amplitude_C),
        .out(volume_C)
        );

    // @TODO: divide master by 3 instead of 2
    localparam MASTER_ACCUMULATOR_BITS = CHANNEL_OUTPUT_BITS + 1;
    localparam MASTER_MAX_OUTPUT_VOLUME = {MASTER_OUTPUT_BITS{1'b1}};
    wire [MASTER_ACCUMULATOR_BITS-1:0] master;
    wire master_overflow;
    assign { master_overflow, master } = volume_A + volume_B + volume_C; // sum all channels
    assign uo_out[MASTER_OUTPUT_BITS-1:0] = 
        (master_overflow == 0) ? master[MASTER_ACCUMULATOR_BITS-1 -: MASTER_OUTPUT_BITS] :  // pass highest MASTER_OUTPUT_BITS to the DAC output pins
                                 MASTER_MAX_OUTPUT_VOLUME;                                  // ALSO prevent value wraparound in the master output

    // PWM outputs
    pwm #(.VALUE_BITS(CHANNEL_OUTPUT_BITS)) pwm_A (
        .clk(clk),
        .reset(reset),
        .value(volume_A),
        .out(uio_out[4])
        );

    pwm #(.VALUE_BITS(CHANNEL_OUTPUT_BITS)) pwm_B (
        .clk(clk),
        .reset(reset),
        .value(volume_B),
        .out(uio_out[5])
        );

    pwm #(.VALUE_BITS(CHANNEL_OUTPUT_BITS)) pwm_C (
        .clk(clk),
        .reset(reset),
        .value(volume_C),
        .out(uio_out[6])
        );

    pwm #(.VALUE_BITS(MASTER_ACCUMULATOR_BITS)) pwm_master (
        .clk(clk),
        .reset(reset),
        .value(master),
        .out(uio_out[7])
        );
    
endmodule
