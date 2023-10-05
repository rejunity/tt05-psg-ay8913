// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.1 Tone Generator Control
// [..] the lowest period value is 000000000001 (divide by 1)

// NOTE despite AY-3-891x manual stating that the tone counter is counted down
// 1) reverse engineering: https://github.com/lvd2/ay-3-8910_reverse_engineered and
// 2) studies of the chip output according to comments in MAME implementation,
//    line 84 https://github.com/mamedev/mame/blob/master/src/devices/sound/ay8910.cpp
// both determined that tone and noise counters are counted UP!

module tone #( parameter COUNTER_BITS = 12 ) (
    input  wire clk,
    input  wire reset,

    input  wire [COUNTER_BITS-1:0]  compare,

    output wire out
);
    reg [COUNTER_BITS-1:0] counter;
    reg state;

    always @(posedge clk) begin
        if (reset) begin
            counter <= 1;
            state <= 0;
        end else begin
            if (counter <= 1) begin
                counter <= compare;         // reset counter
                state <= ~state;            // flip output state
            end else
                counter <= counter - 1'b1; // @TODO: most likely must be upcounting
        end
    end

    assign out = state;
endmodule
