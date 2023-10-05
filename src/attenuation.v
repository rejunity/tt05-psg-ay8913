/* verilator lint_off REALCVT */

// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.7 D/A Converter Operation
// 
// Steps from the diagram: 1V, .707V, .5V, .303V (?), .25V, .1515V (?), .125V .. (not specified) .. 0V


// https://github.com/lvd2/ay-3-8910_reverse_engineered/blob/master/rtl/render/aytab.v
// assign tbl[ 0] = 16'h0000;
// assign tbl[ 1] = 16'h0290;
// assign tbl[ 2] = 16'h03B0;
// assign tbl[ 3] = 16'h0560;
// assign tbl[ 4] = 16'h07E0;
// assign tbl[ 5] = 16'h0BB0;
// assign tbl[ 6] = 16'h1080;
// assign tbl[ 7] = 16'h1B80;
// assign tbl[ 8] = 16'h2070;
// assign tbl[ 9] = 16'h3480;
// assign tbl[10] = 16'h4AD0;
// assign tbl[11] = 16'h5F70;
// assign tbl[12] = 16'h7E10;
// assign tbl[13] = 16'hA2A0;
// assign tbl[14] = 16'hCE40;
// assign tbl[15] = 16'hFFFF;

module attenuation #( parameter CONTROL_BITS = 4, parameter VOLUME_BITS = 15 ) (
    input  wire in,
    input  wire [CONTROL_BITS-1:0] control,
    output reg  [VOLUME_BITS-1:0] out
);
    localparam MAX_VOLUME = {VOLUME_BITS{1'b1}};
    `define ATLEAST1(i) (i>0 ? i : 1)
    always @(*) begin
        case(in ? control : -1) // if in == 0, output is made 0 via the default branch in case statement

            // @TODO: case numbers probably should be reversed!
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

