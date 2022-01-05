//10-12-05
//Vouzis Panagiotis
//I added the last case on line 217 where it is checked whether one of the operands is zero
//so the other one is returne.

`timescale 1ns/100ps

`define wordlength 16
`define f_co	 9
`define k_co	 6
`define j_co 	 5
`define debug  0

module LNSAddSub(x,y,r);
input [`wordlength-1:0] x;
input [`wordlength-1:0] y;
output [`wordlength-1:0] r;

wire [`wordlength-1:0] x_y,y_x;
wire [`wordlength-2:0] z;
wire [`wordlength-2:0] mux_A;
wire SignZa,IsSub,Special,Special2,Special3,IsEssZero;
assign IsSub=x[`wordlength-1]^y[`wordlength-1];



assign x_y = {{x[`wordlength-2]},x[`wordlength-2:0]}-{{y[`wordlength-2]},y[`wordlength-2:0]};
assign y_x = {{y[`wordlength-2]},y[`wordlength-2:0]}-{{x[`wordlength-2]},x[`wordlength-2:0]};

/*always
begin
	#1 if(`debug)
		begin
		$display("x=%b, x=%d, x=%f, y=%b, y=%d, y=%f \n",x,x,lnstoreal(x),y,y,lnstoreal(y));
	 	$display("x-y=%f, x-y=%b, y-x=%f, y-x=%b\n",lnstoreal(x_y),x_y,lnstoreal(y_x),y_x);
	end
end*/

assign SignZa = x_y[`wordlength-1];
assign z = SignZa?x_y[`wordlength-2:0]:y_x[`wordlength-2:0];
/*
always
begin
	#1 if(`debug) $display("z_real=%f, z=%b, and SignZa=%b",lnstoreal(z),z,SignZa);
end */


wire [`k_co+`f_co-`j_co-1:0] zh_co=z[`wordlength-2:`j_co];
wire [`j_co-1:0] zl_co=z[`j_co-1:0];
assign Special = (zh_co==10'b1111111111)?1:0;//Special case 2:  zh_co=-dh
assign Special2 = (z[`wordlength-2:0]==15'b111111111000000)?1:0;//Special case 1: z=-2dh
assign Special3 = x[14:0]==y[14:0];

wire [14:0] zEssZero = 15'b110111000000000;
assign IsEssZero = z<zEssZero&&z!=15'b000000000000000;
assign mux_A = ((SignZa&(~IsSub|IsEssZero|(Special|Special2)))|(~SignZa&(IsSub&~IsEssZero&~(Special|Special2))))?y:x;
/*
always
begin
		#1 if(`debug)   $display("z=%d, zh_co=%b, zh_co=%d, zl_co=%b, zl_co=%d, Mux_A=%b\n",z, zh_co,zh_co,zl_co,zl_co,mux_A);
end*/

wire [`wordlength-2:0] f1,f2,zDif;
F1 F1_inst(zh_co,f1);
F2 F2_inst(zl_co,f2);

/*
always
begin
		#1 if(`debug)
			begin
		 		$display ("z=%b ,z=%d, zess=%b, zess=%d, zh=%b zl=%b\n",z,z,zEssZero,zEssZero,mux_B[`wordlength-3:6],mux_B[5:0]);
		 		$display ("IsSub=%b SignZa=%b,Special=%b, Special2=%b, Special3=%b, IsEssZero=%b\n",IsSub,SignZa,Special,Special2,Special3,IsEssZero);
		 	end
end


always
begin
		#1 if(`debug)  $display("F1=%b, F1=%d, F2=%b, F2=%d\n",f1,f1,f2,f2);
end
  */
assign zDif = f2-f1-z;
    /*
always
begin
		#1 if(`debug)  $display("zDif=%b, zdif=%d \n",zDif,zDif);
end	 */


reg [`wordlength-2:0] mux_B;
always @(IsSub or IsEssZero or Special or zDif or z or zEssZero)

case ({IsSub,IsEssZero|Special})
	3'b11 : mux_B = zEssZero; //Essential Zero
	3'b10 : mux_B = zDif;
	default : mux_B = z;
endcase

wire [`wordlength-2:0] sb_out,sb_out_temp;

/*
always
begin
		#1 if(`debug)  $display("mux_B=%b, mux_B=%d\n",mux_B,mux_B);
end*/

sb sb_inst(mux_B[`wordlength-3:6],mux_B[5:0],sb_out_temp);

assign sb_out=IsEssZero?0:sb_out_temp;
/*
always
begin
		#1 if(`debug) $display("sb_out=%b, sb_out=%d \n",sb_out,sb_out);
end	*/

reg [`wordlength-2:0] mux_C;
always @(IsSub or IsEssZero or Special or f1 or f2)
case ({IsEssZero|~IsSub,Special})
	2'b11 : mux_C = 15'b0000_0000_0000_000;
	2'b10 : mux_C = 15'b0000_0000_0000_000;
	2'b01 : mux_C = f2;
	default : mux_C = f1;
endcase
   /*
always
begin
		#1 if(`debug) $display("mux_A=%b, mux_A=%d \n",mux_A,mux_A);
end

always
begin
		#1 if(`debug) $display("mux_C=%b, mux_C=%d \n",mux_C,mux_C);
end	*/


reg [`wordlength-2:0] op1,op2,op3;
always @(mux_C or mux_A or sb_out or f2 or Special or Special2 or IsSub)
case ({Special&IsSub,Special2&IsSub})
	2'b00:begin op1=mux_C; op2={1'b0,(sb_out)>>2}; op3=mux_A; end
	2'b10:begin op1=f2; op2=0; op3=mux_A; end
	2'b01:begin op1=-1839; op2=0; op3=mux_A; end
	default :begin op1=mux_C; op2={1'b0,(sb_out)>>2}; op3=mux_A; end
endcase

wire [`wordlength-2:0] temp_r;
assign temp_r= op1+op2+op3;



/*reg [`wordlength-2:0] temp_r;
always @(mux_C or mux_A or sb_out or f2 or Special or Special2 or IsSub)
case ({Special&IsSub,Special2&IsSub})
	2'b00: temp_r= mux_C + {1'b0,(sb_out)>>2} + mux_A;
	2'b10: temp_r= mux_A+f2;
	2'b01: temp_r= mux_A-1839;
	default : temp_r= mux_C + mux_A + {1'b0,(sb_out)>>2};
endcase*/



	  /*
always
begin
		#1 if(`debug) $display("temp_r=%b, temp_r=%d, f2=%b \n",temp_r,temp_r,f2);
end	    */

//This always block takes care of the case that overflow may occur,
//and trancates the final result
reg [`wordlength-2:0] saturated_r;
always @(IsSub or temp_r or sb_out or mux_A or x or y or op1 or op3)
begin
	if(IsSub==0)
	begin //If the two operands have the same sign but the final result has different sign then overflow has occured
		if (sb_out[`wordlength-2]==mux_A[`wordlength-2] && temp_r[`wordlength-2]!=sb_out[`wordlength-2])
		begin
				saturated_r=sb_out[14]?15'b100000000000000:15'b011111111111111;
		end else begin
			saturated_r=temp_r;
		end
	end else begin
		if(op1[`wordlength-2]==op3[`wordlength-2] && temp_r[`wordlength-2]!=op1[`wordlength-2])
		begin
			saturated_r=op1[14]?15'b100000000000000:15'b011111111111111;
		end else begin
			saturated_r=temp_r;
		end
	end
end



//This always block takes care of the case that x and y are equal.
//If IsSub==1 then the final result has to be zero, thus the smallest possible logarithm.
//If IsSub==0 then 1.0 has to be added to any of x or y (since they are equal).
//However, there exists the case that the addition of 1.0 may cause overflow,
//so this case is covered here.
reg [`wordlength-2:0] temp_r2;
always@(Special3 or IsSub or mux_A or saturated_r)
begin
	if(Special3==1)
	begin
		if(IsSub==1)
			temp_r2[`wordlength-2:0]=15'b100000000000000;
		else
			if (mux_A[`wordlength-2]==1)//mux_A is negative so there is not chance of overflow
				temp_r2[`wordlength-2:0]=mux_A+15'b000001000000000;
			else if(mux_A<15871) //mux_A is positive but smaller that 16300 so there is not chance of overflow
				temp_r2[`wordlength-2:0]=mux_A+15'b000001000000000;
			else
				temp_r2[`wordlength-2:0]=15'b011111111111111;
	end else begin
			temp_r2[`wordlength-2:0]=saturated_r;
	end
end

assign r[`wordlength-2:0]= (y==15'h4000)?x[`wordlength-2:0]:((x==15'h4000)?y[`wordlength-2:0]:temp_r2);
//assign r[`wordlength-2:0]= temp_r2;
		/*
always
begin
		#1 if(`debug) $display("saturated_r=%b, temp_r2=%b \n",saturated_r,temp_r2);
end		  */



assign r[`wordlength-1] = (Special3&IsSub)?0:(SignZa?y[`wordlength-1]:x[`wordlength-1]);

/*
always
begin
		#1 if(`debug) $display("r=%b, r=%d, r=%f \n",r,r,lnstoreal(r));
end*/

endmodule