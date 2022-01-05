`timescale 1ns/100ps

module lnspipe(sysclk, alua0, alub0, aluc0, alur2);
  input sysclk;
  input [15:0] alua0, alub0, aluc0;
  output [15:0] alur2;

  wire [15:0] alua0, alub0, aluc0;

  function [15:0] lns_mul;
    input [15:0] x,y;
    reg [15:0] r;
    begin
      //zero??
      r = {x[14],x[14:0]} + {y[14],y[14:0]};//sign extension

      if 		((x[14:0]==15'h4000) || (y[14:0]==15'h4000))
      	lns_mul = 16'h4000;
			else if      ((r[15] == 1) && (r[14] == 0))
        lns_mul = {x[15]^y[15],15'h4000};
      else if ((r[15] == 0) && (r[14] == 1))
        lns_mul = {x[15]^y[15],15'h3fff};
      else
        lns_mul = {x[15]^y[15],r[14:0]};
    end
  endfunction

  reg [15:0] alur1, alur2;
  wire[15:0] alur0;
  wire [15:0] alup0 = lns_mul(alub0, aluc0);
  LNSAddSub LNSAddSub_inst(alua0,alup0,alur0);


  `ifdef DEBUG_EVERY_PIPE
     always @(alur0)
      begin
        $display(convert.lnstoreal(alua0)," (",alua0,")+",
                 convert.lnstoreal(alup0)," (",alup0,")=",
                 convert.lnstoreal(alur0)," (",alur0,") t=",$time);
      end
  `endif

  always @(posedge sysclk)
    begin
      alur2 <=  alur1;
      alur1 <=  alur0;
    end

endmodule
