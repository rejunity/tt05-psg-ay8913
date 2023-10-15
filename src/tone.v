// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.1 Tone Generator Control
// [..] the lowest period value is 000000000001 (divide by 1)

// NOTE despite AY-3-891x manual stating that the tone counter is counted down
// 1) reverse engineering: https://github.com/lvd2/ay-3-8910_reverse_engineered
// and
// 2) studies of the chip output according to comments in MAME implementation,
//    line 84 https://github.com/mamedev/mame/blob/master/src/devices/sound/ay8910.cpp
// both determined that tone and noise counters are counted UP!


// Effect of counting UP is such that changing period register will have an immediate effect.
// In contrast counting down delays the effect of the period change until the next wave cycle.
//
//  Initial condition: Period register = 4
//   |
//   v
//   1234 1234 12 12 12 12 12 12 12 12 12 12 12345678              <- counter
//        ----    --    --    --    --    --          ---
//       |    | x|  |  |  |  |  |  |  |  |  | x      |    . . .    <- state flip-flop
//   ----      --    --    --    --    --    --------
//              ^                             ^  
//              |                             |
//      write 2 to Period register     write 8 to Period register
//       has an immediate effect,       has an immediate effect,
//     shortening the current wave!   prolonging the current wave!

module tone #( parameter PERIOD_BITS = 12 ) ( // @TODO: extract counter into a separate model and use in tone, noise & envelope
    input  wire clk,
    input  wire reset,

    input  wire [PERIOD_BITS-1:0]  period,

    output wire out
);
    reg [PERIOD_BITS-1:0] counter;
    reg state;

    always @(posedge clk) begin
        if (reset) begin
            counter <= 1;
            state <= 0;
        end else begin
            if (counter >= period) begin    // real AY-3-891x uses "carry-out" signal from the comparator to reset counter
                counter <= 1;               // reset counter to 1
                                            // @INVESTIGATE what UP_RST means in reverse engineered AY-3-891x schematics [see lvd ay_model_counter]
                                            // .UP_RST(0) is present on first flip-flop on ALL the counter chains: tone, noise & envelope!
                                            // However .UP_RST(0) is NOT present on the internal envelope counter that definetely is counting from _0_ to 15
                                                //  // first flipflop
                                                //  ay_model_clk_ff #( .UP_RST(0) ) counter_bit_0
                                            //
                                            // There are two options with real AY-3-891x upon counter reset, either
                                            // A) counter's first flip-flop is set to 1 due to .UP_RST(0)
                                            // OR
                                            // B) counter is reset to 0, but since real AY-3-819x use two-phase clock f1 and /f1
                                            // it might increase the counter on f1, but compare to period on /f1.
                state <= ~state;            // flip output state
            end else
                counter <= counter + 1'b1;
        end
    end

    assign out = state;
endmodule
