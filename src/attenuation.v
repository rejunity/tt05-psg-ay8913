/* verilator lint_off REALCVT */

// FROM General Instruments AY-3-8910 / 8912 Programmable Sound Generator (PSG) data Manual.
// Section 3.7 D/A Converter Operation
// 
// Steps from the diagram: 1V, .707V, .5V, .303V (?), .25V, .1515V (?), .125V .. (not specified) .. 0V


// https://github.com/lvd2/ay-3-8910_reverse_engineered/blob/master/rtl/render/aytab.v
// v/0xFFFF for v in [0x0000, 0x0290, 0x03B0, 0x0560, 0x07E0, 0x0BB0, 0x1080, 0x1B80, 0x2070, 0x3480, 0x4AD0, 0x5F70, 0x7E10, 0xA2A0, 0xCE40, 0xFFFF]]

// assign tbl[ 0] = 16'h0000;
// assign tbl[ 1] = 16'h0290;      // 0,010009918364233
// assign tbl[ 2] = 16'h03B0;      // 0,014404516670481
// assign tbl[ 3] = 16'h0560;      // 0,021054242215592
// assign tbl[ 4] = 16'h07E0;      // 0,030846913013541
// assign tbl[ 5] = 16'h0BB0;      // 0,045780735980415
// assign tbl[ 6] = 16'h1080;      // 0,064631627266468
// assign tbl[ 7] = 16'h1B80;      // 0,107719378777446
// assign tbl[ 8] = 16'h2070;      // 0,127059903603397
// assign tbl[ 9] = 16'h3480;      // 0,205646086756943
// assign tbl[10] = 16'h4AD0;      // 0,293045673628644
// assign tbl[11] = 16'h5F70;      // 0,373835207711728
// assign tbl[12] = 16'h7E10;      // 0,493795424986612
// assign tbl[13] = 16'hA2A0;      // 0,637013235406625
// assign tbl[14] = 16'hCE40;      // 0,807895340830847
// assign tbl[15] = 16'hFFFF;

// 0.0,
// 0.010009918364232854,
// 0.014404516670481423,
// 0.020996414129854278,
// 0.030762188143739988,
// 0.04565499351491569,
// 0.06445410849164569,
// 0.10742351415274282,
// 0.12671091783016708,
// 0.2050812542915999,
// 0.2922407873655299,
// 0.372808422980087,
// 0.49243915465018695,
// 0.6352635996032654,
// 0.8056763561455711,
// 1.

// struct ay_ym_param
//     {
//         double r_up;
//         double r_down;
//         int    res_count;
//         double res[32];
//     };

// static const ay8910_device::ay_ym_param ay8910_param =
// {
//     800000, 8000000,
//     16,
//     { 15950, 15350, 15090, 14760, 14275, 13620, 12890, 11370,
//         10600,  8590,  7190,  5985,  4820,  3945,  3017,  2345 }
// };

// @TODO: perhaps rename to volume or amplitude to match AY manuals
// @TODO: python script and convert MAME params into amplitude levels, compare with lvd version

module attenuation #( parameter CONTROL_BITS = 4, parameter VOLUME_BITS = 15 ) (
    input  wire in,
    input  wire [CONTROL_BITS-1:0] control,
    output reg  [VOLUME_BITS-1:0] out
);
    localparam real MAX_VOLUME = (1 << VOLUME_BITS) - 1;
    `define ATLEAST1(i) ($rtoi(i)>1 ? $rtoi(i) : 1)
    always @(*) begin
        case(in ? control : 0)

            // // https://github.com/lvd2/ay-3-8910_reverse_engineered/blob/master/rtl/render/aytab.v
            // 0:  out =                        0;
            // 1:  out = `ATLEAST1(MAX_VOLUME * 0.010009918364233);
            // 2:  out = `ATLEAST1(MAX_VOLUME * 0.014404516670481);
            // 3:  out = `ATLEAST1(MAX_VOLUME * 0.021054242215592);
            // 4:  out = `ATLEAST1(MAX_VOLUME * 0.030846913013541);
            // 5:  out = `ATLEAST1(MAX_VOLUME * 0.045780735980415);
            // 6:  out = `ATLEAST1(MAX_VOLUME * 0.064631627266468);
            // 7:  out = `ATLEAST1(MAX_VOLUME * 0.107719378777446);
            // 8:  out = `ATLEAST1(MAX_VOLUME * 0.127059903603397);
            // 9:  out = `ATLEAST1(MAX_VOLUME * 0.205646086756943);
            // 10: out = `ATLEAST1(MAX_VOLUME * 0.293045673628644);
            // 11: out = `ATLEAST1(MAX_VOLUME * 0.373835207711728);
            // 12: out = `ATLEAST1(MAX_VOLUME * 0.493795424986612);
            // 13: out = `ATLEAST1(MAX_VOLUME * 0.637013235406625);
            // 14: out = `ATLEAST1(MAX_VOLUME * 0.807895340830847);
            // 15: out = `ATLEAST1(MAX_VOLUME * 1.0);

            //  0: out = 12'h000;
            //  1: out = 12'h029;
            //  2: out = 12'h03B;
            //  3: out = 12'h056;
            //  4: out = 12'h07E;
            //  5: out = 12'h0BB;
            //  6: out = 12'h108;
            //  7: out = 12'h1B8;
            //  8: out = 12'h207;
            //  9: out = 12'h348;
            // 10: out = 12'h4AD;
            // 11: out = 12'h5F7;
            // 12: out = 12'h7E1;
            // 13: out = 12'hA2A;
            // 14: out = 12'hCE4;
            // 15: out = 12'hFFF;

            //  0: out = 8'h00;
            //  1: out = 8'h03;
            //  2: out = 8'h04;
            //  3: out = 8'h06;
            //  4: out = 8'h08;
            //  5: out = 8'h0C;
            //  6: out = 8'h11;
            //  7: out = 8'h1C;
            //  8: out = 8'h20;
            //  9: out = 8'h35;
            // 10: out = 8'h4B;
            // 11: out = 8'h5F;
            // 12: out = 8'h7E;
            // 13: out = 8'hA3;
            // 14: out = 8'hCE;
            // 15: out = 8'hFF;

            // YM2149, numbers from the manual, every 2nd step is taken
            // YM2149 32 steps: 1V, .841, .707, .595, .5, .42, .354, .297, .25, .21, .177, .149, .125
            15: out = `ATLEAST1(MAX_VOLUME * 1.0  );
            14: out = `ATLEAST1(MAX_VOLUME * 0.707);
            13: out = `ATLEAST1(MAX_VOLUME * 0.5  );
            12: out = `ATLEAST1(MAX_VOLUME * 0.354);
            11: out = `ATLEAST1(MAX_VOLUME * 0.25 );
            10: out = `ATLEAST1(MAX_VOLUME * 0.177);   
            9:  out = `ATLEAST1(MAX_VOLUME * 0.125);
            8:  out = `ATLEAST1(MAX_VOLUME * 0.089);
            7:  out = `ATLEAST1(MAX_VOLUME * 0.063);
            6:  out = `ATLEAST1(MAX_VOLUME * 0.045);
            5:  out = `ATLEAST1(MAX_VOLUME * 0.032);
            4:  out = `ATLEAST1(MAX_VOLUME * 0.023);
            3:  out = `ATLEAST1(MAX_VOLUME * 0.016);
            2:  out = `ATLEAST1(MAX_VOLUME * 0.012);
            1:  out = `ATLEAST1(MAX_VOLUME * 0.008);
            0:  out =                        0;

            // Somewhat weird numbers from the original AY-3-8190 documentation
            // 15: out = `ATLEAST1(MAX_VOLUME * 1.0);
            // 14: out = `ATLEAST1(MAX_VOLUME * 0.707);
            // 13: out = `ATLEAST1(MAX_VOLUME * 0.5);
            // 12: out = `ATLEAST1(MAX_VOLUME * 0.303);
            // 11: out = `ATLEAST1(MAX_VOLUME * 0.25);
            // 10: out = `ATLEAST1(MAX_VOLUME * 0.1515);   
            // 9:  out = `ATLEAST1(MAX_VOLUME * 0.125);
            // 8:  out = `ATLEAST1(MAX_VOLUME * 0.07575);
            // 7:  out = `ATLEAST1(MAX_VOLUME * 0.0625);
            // 6:  out = `ATLEAST1(MAX_VOLUME * 0.037875);
            // 5:  out = `ATLEAST1(MAX_VOLUME * 0.03125);
            // 4:  out = `ATLEAST1(MAX_VOLUME * 0.0189375);
            // 3:  out = `ATLEAST1(MAX_VOLUME * 0.015625);
            // 2:  out = `ATLEAST1(MAX_VOLUME * 0.00946875);
            // 1:  out = `ATLEAST1(MAX_VOLUME * 0.0078125);
            // 1:  out =                        0;
        endcase
        `undef ATLEAST1
    end
endmodule

