module signal_edge(
    input  wire clk,
    input  wire reset,
    input  wire signal,
    output wire on_posedge,
    output wire on_negedge,
    output wire on_edge
);
    reg previous_signal_state;
    always @(posedge clk) begin
        if (reset)
            previous_signal_state <= 0;
        else
            previous_signal_state <= signal;
    end
    
    assign on_edge    = (previous_signal_state != signal);
    assign on_posedge = (previous_signal_state != signal &&  signal);
    assign on_negedge = (previous_signal_state != signal && !signal);
endmodule
