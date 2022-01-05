`timescale 1ns/100ps

module sb(Zh,Zl,sbz);
	input [7:0]Zh;
	input [5:0] Zl;
	output [14:0] sbz;
    wire [14:0] sbzh;
    wire [6:0] slope;
    wire [15:0] prod = slope*Zl;
	  assign sbzh[14:12]=0;
    funcRom f1(sbzh[11:0],Zh);
    slopeRom s1(slope,Zh);
    assign sbz = sbzh+{1'b0,(prod)>>6};

	/*always
	begin
		#1 $display("zh=%b zl=%b slope = %d sbzh=%d sbz=%d\n",Zh,Zl,slope,sbzh,sbz);

	//	#10000 $display("slope is %d abz is %d\n",slope,sbzh);
	end*/
endmodule
/*
module lns_adder(x,y,out);
	input [14:0]x,y;
	output [14:0]out;
	//wire [14:0] z1;

    //wire [6:0] Zh;//7 bit vector of z.
    //wire [5:0] Zl; //6 bit vector of it.

    wire [14:0] sbz;
    wire [14:0] z1=x-y;
    wire [14:0] z2=y-x;
    wire [13:0] z=z1[14]?z1[13:0]:z2[13:0];
	//now z is always positive.
    wire [7:0] Zh=z[13:6];
    wire [5:0] Zl=z[5:0];  //these set the values I think.
    sb mysb(Zh,Zl,sbz);

    wire [25:0] tmp;

    assign tmp = z1[14]?
		y+{1'b0, (sbz ) >>2} :
		x+{1'b0, (sbz ) >>2} ;
    assign out=tmp[14:0];
		//lns_add = realtolns(lnstoreal(x) + lnstoreal(y));

endmodule
module lns();


//the MSB of the vector isn't needed...
  function [14:0] lns_add;
    input [14:0] x;
    input [14:0] y;

//    wire [14:0] x;
//    wire [14:0] y;

	begin


    	end
  endfunction

  function [12:0] sb;
	input [7:0] zH;
	input [5:0] zL;

	begin

	end
  endfunction

  function real lnstoreal;
    input [15:0] lnsval;

    reg [15:0] lns;
    real power,prod;
    integer i;

    begin
      if (lnsval == 16'h4000)
        lnstoreal = 0.0;
      else
      begin
        if (lnsval[14])
          lns = -lnsval;
        else
          lns = lnsval;
        prod = 1.0;
        power = 1.35471989;
        power = power / 1000.0;
        power = power + 1.0;
        for (i=1; i<=15; i=i+1)
          begin
            if (lns[0])
              prod = prod * power;
            lns = lns >> 1;
            power = power * power;
          end
        if (lnsval[15])
          prod = - prod;
        if (lnsval[14])
          lnstoreal = 1.0/prod;
        else
          lnstoreal = prod;
      end
    end
  endfunction

  function real rootof2;
    input n;
    integer n;
    real power;
    integer i;
    begin
      power = 1.35471989;
      power = power / 1000.0;
      power = power + 1.0;
      for (i=-9; i<=n; i=i+1)
        begin
          rootof2 = power;
          power = power * power;
        end
    end
  endfunction



  function [15:0] realtolns;
    input realval;
    real realval;
    real re,reabs;
    reg [15:0] lns;
    integer i;
    begin
      if (realval == 0.0)
        realtolns = 16'h4000;
      else
      begin
        if (realval < 0.0)
          reabs = -realval;
        else
          reabs = realval;
        if (reabs<1.0)
          re = 1.0/reabs;
        else
          re = reabs;
        lns = 0;
        for (i=4; i>=-9; i=i-1)
          begin
            if (re > rootof2(i))
              begin
                re = re/rootof2(i);
                lns = (lns << 1) | 1;
              end
            else
              lns = lns << 1;
          end
        if (reabs < 1.0)
          lns = -lns;
        if (realval < 0.0)
          realtolns = 16'h8000 | lns;
        else
          realtolns = 16'h7fff & lns;
      end
    end
  endfunction

integer i;
reg [15:0]a1;
reg [15:0]a2;
reg [15:0]a3;
wire [15:0]added;
assign added[15]=0;
lns_adder la(a1[14:0],a2[14:0],added[14:0]);
initial
	begin
		a1=realtolns(60.0);
		a2=realtolns(103.0);
		a3=realtolns(lnstoreal(a1)+lnstoreal(a2));
		//added=lns_add(a1[14:0],a2[14:0]);

		#5000000 $display("program starts here %f %f.",lnstoreal(added),lnstoreal(a3));
		a1=realtolns(163.0);
		#1000000 $display("a1=%d %f\n",a1,lnstoreal(a1));

	end

always
	begin
		#1000000 $display("added=%d\n",added);
	end
endmodule*/