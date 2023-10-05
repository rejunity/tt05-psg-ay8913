// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.1 Tone Generator Control
// ...
// Note also that due to the design technique used in the Tone Period count-down,
// the lowest period value is 000000000001 (divide by 1)

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
                counter <= counter - 1'b1;
        end
    end

    assign out = state;
endmodule
