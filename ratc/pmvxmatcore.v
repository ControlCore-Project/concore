`include "concore.v"


`timescale 1ns/100ps
`include "commands.v"
`include "matrixLNSproc.v"
`include "matrixprocRAM.v"
`include "lnspipe.v"
`include "LNSAddSub.v"
`include "F1.v"
`include "F2.v"
`include "rom.v"
`include "sb.v"

`define BITS_MAXMAT 4
`define MAXMAT (1<<`BITS_MAXMAT)

`define N 8'd2
`define M 8'd6
`define P 5

`define ADDR_A 0
`define ADDR_B 48
`define ADDR_C 84
`define ADDR_D 96
`define ADDR_X 36
`define ADDR_U 42
`define ADDR_YM 114
`define ADDR_NEWX 108


module testMPC;
  reg sysclk, reset;
  reg [15:0] din;
  wire [15:0] dout;
  reg cs,rd,wr,dataORstatus;
  matrixLNSproc matrixLNSproc_inst(din,dout,cs,rd,wr, dataORstatus, sysclk, reset);

initial
    begin
         reset = 0;
      #1 reset = 1;
      #1 reset = 0;
    end

initial    sysclk = 0;
always #50 sysclk = ~sysclk;

`include "functions.v"
`include "yuyumatrixdata2.v"

//reg [15:0] element,pivot, x;

integer Nsim = 150;
reg [8*13-1:0] init_simtime_u = "[0.0,0.0,0.0]";
reg [8*29-1:0] init_simtime_ym = "[0.0,0.0,0.0,0.0,0.0,0.0,0.0]";

initial
 begin
  while(concore.simtime<Nsim)
   begin
      while (concore.unchanged(0))
        begin
//$display("here");
           concore.readdata(1,"u",init_simtime_u);
        end
      $display("u=",concore.data[0]);
      $display(10000.0*concore.data[1]);
      $display(concore.data[2]);
      $display(10000.0*concore.data[3]);
      $display(concore.data[4]);
      $display(10000.0*concore.data[5]);
      //$stop;
      matrixLNSproc_inst.matrixproc_inst.m[`ADDR_U+0]=realtolns(concore.data[0]);
      matrixLNSproc_inst.matrixproc_inst.m[`ADDR_U+1]=realtolns(concore.data[1]);
      matrixLNSproc_inst.matrixproc_inst.m[`ADDR_U+2]=realtolns(concore.data[2]);
      matrixLNSproc_inst.matrixproc_inst.m[`ADDR_U+3]=realtolns(concore.data[3]);
      matrixLNSproc_inst.matrixproc_inst.m[`ADDR_U+4]=realtolns(concore.data[4]);
      matrixLNSproc_inst.matrixproc_inst.m[`ADDR_U+5]=realtolns(concore.data[5]);

      initialize_wrapper;

      send_command(`COMMAND_RESET);   // reset
      send_command(`COMMAND_SET_RC);
      send_data({8'd6,8'd6});         //n_row,n_col
      wait_status;
      send_command(`COMMAND_STORE_CLEAR_A);
      send_data(250);         //n_row,n_col
      wait_status;
      send_command(`COMMAND_SET_N);
      send_data(`M);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({`M,`M});
      wait_status;
      send_command(`COMMAND_LOAD_C); //xm
      send_data(`ADDR_A);
      wait_status;
      send_command(`COMMAND_MULVEC_CR_RECT);  //multiply with x
      send_data(`ADDR_X);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({8'd1,`M});
      wait_status;
      send_command(`COMMAND_STORE_CLEAR_VECA); //store Ax
      send_data(`ADDR_NEWX);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({`M,`M});
      wait_status;
      send_command(`COMMAND_LOAD_C); //B
      send_data(`ADDR_B);
      wait_status;
      send_command(`COMMAND_MULVEC_CR_RECT);  //multiply with u
      send_data(`ADDR_U);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({8'd1,`M});
      wait_status;
      send_command(`COMMAND_ADDVEC_A);//add vector Ax
      send_data(`ADDR_NEWX);         //a=Ax+Bu
      send_data(0);
      wait_status;
/*
			$write("A=Ax+Bu (hex)");$display;
      send_command(`COMMAND_OUTPUT_A);
      rcv_matrect(`M,1);
      print_matrect_hex(`M,1);
			$write("A=Ax+Bu");$display;
      print_matrect(`M,1);
*/
      send_command(`COMMAND_STORE_CLEAR_VECA); //store Ax
      send_data(`ADDR_NEWX);
      wait_status;
/*
			$display("%h %h %h %h %h %h",
               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_NEWX],
               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_NEWX+1],
               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_NEWX+2],
               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_NEWX+3],
               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_NEWX+4],
               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_NEWX+5]); 

      send_command(`COMMAND_LOAD_A);
      send_data(`ADDR_X);
      wait_status;

			$write("A=x (hex)");$display;
      send_command(`COMMAND_OUTPUT_A);
      rcv_matrect(`M,1);
      print_matrect_hex(`M,1);
			$write("A=x");$display;
      print_matrect(`M,1);
      // $stop;
*/
      send_command(`COMMAND_SET_N);
      send_data(2);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({8'd2,`M});
      wait_status;
      send_command(`COMMAND_STORE_CLEAR_A);
      send_data(250);         //n_row,n_col
      wait_status;
      send_command(`COMMAND_LOAD_C); //C
      send_data(`ADDR_C);
      wait_status;
/*
$display("C (hex)");
send_command(`COMMAND_OUTPUT_C);
rcv_matrect(2,`M);
print_matrect_hex(2,`M);
$write("C ");$display;
print_matrect(2,`M);
*/
      send_command(`COMMAND_SET_N);
      send_data(6);
      wait_status;
      send_command(`COMMAND_MULVEC_CR_RECT);  //multiply with x
      send_data(`ADDR_X);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({8'd1,8'd2});
      wait_status;
/*
			$write("A=Cx (hex)");$display;
      send_command(`COMMAND_OUTPUT_A);
      rcv_matrect(2,1);
      print_matrect_hex(2,1);
			$write("A=Cx");$display;
      print_matrect(2,1);
*/
      send_command(`COMMAND_STORE_CLEAR_VECA); //store Cx
      send_data(`ADDR_YM);
      wait_status;
      send_command(`COMMAND_SET_N);
      send_data(2);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({8'd2,`M});
      wait_status;
      send_command(`COMMAND_LOAD_C); //D
      send_data(`ADDR_D);
      wait_status;
      send_command(`COMMAND_SET_N);
      send_data(6);
      wait_status;
      send_command(`COMMAND_MULVEC_CR_RECT);  //multiply with u
      send_data(`ADDR_U);
      wait_status;
      send_command(`COMMAND_SET_RC);
      send_data({8'd1,8'd2});
      wait_status;
/*
			$write("A=Du (hex)");$display;
      send_command(`COMMAND_OUTPUT_A);
      rcv_matrect(2,1);
      print_matrect_hex(2,1);
			$write("A=Du");$display;
      print_matrect(2,1);
      $stop;		
*/
      send_command(`COMMAND_SET_N);
      send_data(2);
      wait_status;
      send_command(`COMMAND_ADDVEC_A);//add vector Cx
      send_data(`ADDR_YM);           //a=Ax+Bu
      send_data(0);
      wait_status;
/*
			$write("A=Cx+Du (hex)");$display;
      send_command(`COMMAND_OUTPUT_A);
      rcv_matrect(2,1);
      print_matrect_hex(2,1);
			$write("A=Cx+Du");$display;
      print_matrect(2,1);
*/
      send_command(`COMMAND_STORE_CLEAR_VECA); //store Cx+Du
      send_data(`ADDR_YM);
      wait_status;
//			$display("%h %h",
//               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_YM],
//               matrixLNSproc_inst.matrixproc_inst.m[`ADDR_YM+1]);
     $write("ym=",
      lnstoreal(matrixLNSproc_inst.matrixproc_inst.m[`ADDR_YM]));
     $display(",",
     lnstoreal(matrixLNSproc_inst.matrixproc_inst.m[`ADDR_YM+1]));
   //$stop;
      concore.data[0]=lnstoreal(matrixLNSproc_inst.matrixproc_inst.m[`ADDR_YM]);
      concore.data[1]=lnstoreal(matrixLNSproc_inst.matrixproc_inst.m[`ADDR_YM+1]);
      concore.datasize = 2;
      concore.writedata(1,"ym",1);
   end
  $display("retry=",concore.retrycount);
 end
endmodule


/*        concore.writedata(1,"ym",1);
      end 
    concore.write(1,"ym",init_simtime_ym);
  end
endmodule
*/

