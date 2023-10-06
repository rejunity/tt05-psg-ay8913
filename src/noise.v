// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.2 Noise Generator Control
// ...
// Note that the 6-bit value in R11 is a period value-the higher the value in the register,
// the lower the resultant noise frequency. Note also that, as with the Tone Period,
// the lowest period value is 00001 (divide by 1); the highest period value is 11111 (divide by 3110).


// @TODO: 6 bit and R11, WHAT?

// https://github.com/lvd2/ay-3-8910_reverse_engineered/blob/master/rtl/ay_model.v
// // noise LFSR
// ay_model_shiftreg noise_shift_reg
// (
//     ._f(_f4),
//     . f( f4),

//     .rst(rst_1),

//     .shift_in( (noise_reg[16] ^ noise_reg[13]) | (~|noise_reg) ),

//     .result( noise_reg )
// );
// //
// assign noise = ~noise_reg[16];


// module ay_model_shiftreg
// #(
//     parameter WIDTH=17
// )
// (
//     input  wire _f,
//     input  wire  f,
//     input  wire rst,

//     input  wire shift_in,
//     output wire [WIDTH-1:0] result
// );
//     wire [WIDTH-1:0] shin;
//     trireg [WIDTH-1:0] l1;
//     trireg [WIDTH-1:0] l2;
//     // shift in
//     assign shin = { l2[WIDTH-2:0], shift_in };
//     assign l1 = rst ? {WIDTH{1'b0}} : (_f ? shin : {WIDTH{1'bZ}});
//     assign l2 = f ? l1 : {WIDTH{1'bZ}};
//     assign result = l2;

// endmodule

// https://github.com/mamedev/mame/blob/master/src/devices/sound/ay8910.h#L266
// inline void noise_rng_tick()
// {
//     // The Random Number Generator of the 8910 is a 17-bit shift
//     // register. The input to the shift register is bit0 XOR bit3
//     // (bit0 is the output). This was verified on AY-3-8910 and YM2149 chips.

//     if (m_feature & PSG_HAS_EXPANDED_MODE) // AY8930 LFSR algorithm is slightly different, verified from manual
//         m_rng = (m_rng >> 1) | ((BIT(m_rng, 0) ^ BIT(m_rng, 2)) << 16);
//     else
//         m_rng = (m_rng >> 1) | ((BIT(m_rng, 0) ^ BIT(m_rng, 3)) << 16);
// }

module noise #( parameter LFSR_BITS = 17, LFSR_TAP0 = 0, LFSR_TAP1 = 1, parameter COUNTER_BITS = 5 ) (
    input  wire clk,
    input  wire reset,
    input  wire restart_noise,

    input  wire [2:0] control,
    input  wire [COUNTER_BITS-1:0] tone_freq,

    output wire  out
);
    localparam MASTER_CLOCK = 16;
    localparam TONE_DIV_2 = 2;

    reg [COUNTER_BITS-1:0] noise_freq;
    always @(posedge clk) begin
        // NF0, NF1 bits
        case(control[1:0])
            2'b00:  noise_freq <= 512 /MASTER_CLOCK/TONE_DIV_2;
            2'b01:  noise_freq <= 1024/MASTER_CLOCK/TONE_DIV_2;
            2'b10:  noise_freq <= 2048/MASTER_CLOCK/TONE_DIV_2;
            2'b11:  noise_freq <= tone_freq;
        endcase
        // FB bit
        is_white_noise <= control[2];
    end

    wire noise_trigger;
    tone #(.COUNTER_BITS(COUNTER_BITS)) tone (
        .clk(clk),
        .reset(reset),
        .period(noise_freq),
        .out(noise_trigger));

    reg is_white_noise;
    reg reset_lfsr;
    reg [LFSR_BITS-1:0] lfsr;
    assign reset_lfsr = reset | restart_noise;
    always @(posedge noise_trigger, posedge reset_lfsr) begin
        if (reset_lfsr) begin
            lfsr <= 1'b1 << (LFSR_BITS-1);
        end else begin
            if (is_white_noise) begin
                lfsr <= {lfsr[LFSR_TAP0] ^ lfsr[LFSR_TAP1], lfsr[LFSR_BITS-1:1]};
            end else begin
                lfsr <= {lfsr[LFSR_TAP0]                  , lfsr[LFSR_BITS-1:1]};
            end
        end
    end

    assign out = lfsr[0];
endmodule
