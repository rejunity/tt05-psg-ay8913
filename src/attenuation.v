/* verilator lint_off REALCVT */

// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.7 D/A Converter Operation
// 
// Steps from the diagram: 1V, .707V, .5V, .303V (?), .25V, .1515V (?), .125V .. (not specified) .. 0V

module attenuation #( parameter CONTROL_BITS = 4, parameter VOLUME_BITS = 15 ) (
    input  wire in,
    input  wire [CONTROL_BITS-1:0] control,
    output reg  [VOLUME_BITS-1:0] out
);
    localparam MAX_VOLUME = {VOLUME_BITS{1'b1}};
    `define ATLEAST1(i) (i>0 ? i : 1)
    always @(*) begin
        case(in ? control : -1) // if in == 0, output is made 0 via the default branch in case statement
            0:  out =           MAX_VOLUME;
            1:  out = `ATLEAST1(MAX_VOLUME * 0.707);          // NOTE: YM2149 32 steps: 1V, .841, .707, .595,
            2:  out = `ATLEAST1(MAX_VOLUME * 0.5);            //                        .5, .42, .354, .297,
            3:  out = `ATLEAST1(MAX_VOLUME * 0.303);          //                        .25, .21, .177, .149,
            4:  out = `ATLEAST1(MAX_VOLUME * 0.25);           //                        .125
            5:  out = `ATLEAST1(MAX_VOLUME * 0.1515);
            6:  out = `ATLEAST1(MAX_VOLUME * 0.125);
            7:  out = `ATLEAST1(MAX_VOLUME * 0.07575);
            8:  out = `ATLEAST1(MAX_VOLUME * 0.0625);
            9:  out = `ATLEAST1(MAX_VOLUME * 0.037875);
            10: out = `ATLEAST1(MAX_VOLUME * 0.03125);
            11: out = `ATLEAST1(MAX_VOLUME * 0.0189375);
            12: out = `ATLEAST1(MAX_VOLUME * 0.015625);
            13: out = `ATLEAST1(MAX_VOLUME * 0.00946875);
            14: out = `ATLEAST1(MAX_VOLUME * 0.0078125);
            // 0.3535, 0.17675, 0.088375, 0.0441875, 0.02209375, 0.011046875,
                default:
                    out = 0;
        endcase
        `undef ATLEAST1
    end
endmodule

