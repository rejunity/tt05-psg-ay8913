// Envelope shapes:
//     Continue
//     | Attack
//     | | Alternate
//     | | | Hold
//     0 0 x x  \___
//     0 1 x x  /___
//     1 0 0 0  \\\\
//     1 0 0 1  \___
//     1 0 1 0  \/\/
//     1 0 1 1  \```
//     1 1 0 0  ////
//     1 1 0 1  /```
//     1 1 1 0  /\/\
//     1 1 1 1  /___

// Continue == 0
//     0 0 x x  \___ -> 1 0 0 1
//     0 1 x x  /___ -> 1 1 1 1
// Hold' = !Continue, Alternate' = Attack

// Hold == 1
//       Attack'
//       | Alternate'
//       0 0 1  \___
//       0 1 1  \```
//       1 0 1  /```
//       1 1 1  /___

module envelope #( parameter PERIOD_BITS = 16, parameter ENVELOPE_BITS = 4 ) (
    input  wire clk,
    input  wire reset,

    input  wire hold,
    input  wire alternate,
    input  wire attack,
    input  wire continue_,

    input  wire [PERIOD_BITS-1:0] period,

    output wire [ENVELOPE_BITS-1:0] out
);
    // handle 'Continue == 0' by mapping to counterpart 'Continue == 1' signals
    // that produce the same envelopes
    //     Continue
    //     | Attack
    //     | | Alternate
    //     | | | Hold
    //     0 0 x x  \___ -> 1 0 0 1
    //     0 1 x x  /___ -> 1 1 1 1
    // if Continue == 0 then Hold' = !Continue, Alternate' = Attack
    wire hold_      =   hold || !continue_;
    wire alternate_ =   continue_ ? alternate : attack;
    wire attack_    =   attack;

    // handle 'Hold == 1'
    //       Attack'
    //       | Alternate'
    //       0 0 1  \___
    //       0 1 1  \```
    //       1 0 1  /```
    //       1 1 1  /___
    wire hold__     =   hold_;
    wire alternate__=   hold_ ? ~alternate_ : alternate_;
    wire attack__   =   attack_;

    wire trigger;
    tone #(.PERIOD_BITS(PERIOD_BITS)) tone (
        .clk(clk),
        .reset(reset),
        .period(period),
        .out(trigger));

    wire trigger_posedge;
    signal_edge trigger_edge(
        .clk(clk),
        .reset(reset),
        .signal(trigger),
        .on_posedge(trigger_posedge)
    );

    reg invert_output;
    reg [ENVELOPE_BITS-1:0] envelope_counter;
    reg stop;
    // always @(posedge advance_envelope) begin
    always @(posedge clk) begin
        if (reset) begin
            envelope_counter <= 0;
            stop <= 0;
        end else begin
            if (trigger_posedge)
                if (!(hold__ && stop))
                    {stop, envelope_counter} <= envelope_counter + 1'b1;
        end
    end

    always @(posedge clk) begin
        if (reset)
            invert_output <= !attack__;
        else begin
            if (trigger_posedge && envelope_counter == MAX_VALUE)
                if (alternate__)
                    invert_output <= ~invert_output;
        end
    end


    localparam MAX_VALUE = {ENVELOPE_BITS{1'b1}};
    assign out =
        invert_output ? MAX_VALUE - envelope_counter : envelope_counter;

endmodule
