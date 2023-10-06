// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.2 Noise Generator Control
// ...
// Note that the 6-bit value in R11 is a period value-the higher the value in the register,
// the lower the resultant noise frequency. Note also that, as with the Tone Period,
// the lowest period value is 00001 (divide by 1); the highest period value is 11111 (divide by 3110).

module noise #( parameter LFSR_BITS = 17, LFSR_TAP0 = 0, LFSR_TAP1 = 3, parameter COUNTER_BITS = 5 ) (
    input  wire clk,
    input  wire reset,
    input  wire [COUNTER_BITS-1:0] period,

    output wire  out
);
    wire lfsr_shift_trigger;
    tone #(.COUNTER_BITS(COUNTER_BITS)) tone (
        .clk(clk),
        .reset(reset),
        .period(period),
        .out(lfsr_shift_trigger));

    reg [LFSR_BITS-1:0] lfsr;
    wire is_lfsr_zero = (lfsr == 0); // more readable, but equivalent to the hardware implementation ~(|lfsr)
    wire lfsr_shift_in = (lfsr[LFSR_TAP0] ^ lfsr[LFSR_TAP1]) | is_lfsr_zero; // @TODO: investigate why MAME has only 2 taps XOR. Could that be a bug in MAME?
    always @(posedge lfsr_shift_trigger) begin
        if (reset)
            lfsr <= 0;
        else
            lfsr <= {lfsr_shift_in, lfsr[LFSR_BITS-1:1]};
    end

    assign out = ~lfsr[0];
endmodule
