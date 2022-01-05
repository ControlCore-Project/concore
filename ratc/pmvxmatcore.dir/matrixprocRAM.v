//Matrix processor, pipelined version
//Mark Arnold
//
//  commands for rectangular matrices only partially implemented 12 April 05
//    still need left and right multiply, transpose, etc.

//09-20-05
//Vouzis Panagiotis
//1) I added the command  COMMAND_MUL_CR which multiplys C on the right with a matrix in memory
//2) I added the command  COMMAND_MULVEC_C_RECT which multiplys C on the left with a matrix in memory
//	 For the command COMMAND_MULVEC_C_RECT the limits of the indices used are n and n_col.
//3) I added the command  COMMAND_MULVEC_CR_RECT which multiplys C on the right with a matrix in memory
//   For the command COMMAND_MULVEC_CR_RECT the limits of the indices used are n and n_col.
//4) `define JK {j[`BITS_MAXMAT-1:0],k[`BITS_MAXMAT-1:0]} added. It is used in command COMMAND_MULVEC_CR_RECT
//5) I added the command COMMAND_MUL_SCALAR_A and I changed the line "`define N_ROW...."
//09-21-05
//1) I added the command COMMAND_MUL2_COMP in order to calculate 1/(bar+u)^2+1/(bar-u)^2
//2) I added the command COMMAND_MUL3_COMP in order to calculate 1/(bar+u)^3+1/(bar-u)^3




`timescale 1ns/100ps

`define ENS #1
`define NCLK @(posedge sysclk)
//`define DEBUG_EVERY_CLOCK
//`define DEBUG_EVERY_PIPE
//`define DEBUG_EVERY_COMMAND
//`define DEBUG_EVERY_DATA


`include "commands.v"

`define STARTDI  while (distrb==0) begin @(posedge sysclk)`ENS;end status<=@(posedge sysclk)`BUSY_DI_STATUS
`define FINISHDI while (distrb==1) begin @(posedge sysclk)`ENS;end status<=@(posedge sysclk)`BUSY_PROC_STATUS
`define STARTDO  while (dostrb==0) begin @(posedge sysclk)`ENS;end status<=@(posedge sysclk)`BUSY_DO_STATUS
`define FINISHDO while (dostrb==1) begin @(posedge sysclk)`ENS;end status<=@(posedge sysclk)`BUSY_PROC_STATUS

`define MEMSIZE 64

`define BITS_MAXMAT 3
`define MAXMAT (1<<`BITS_MAXMAT)

`define IJ {i[`BITS_MAXMAT-1:0],j[`BITS_MAXMAT-1:0]}
`define IK {i[`BITS_MAXMAT-1:0],k[`BITS_MAXMAT-1:0]}
`define KJ {k[`BITS_MAXMAT-1:0],j[`BITS_MAXMAT-1:0]}
`define JK {j[`BITS_MAXMAT-1:0],k[`BITS_MAXMAT-1:0]}

`define N_ROW (((command==`COMMAND_MUL_SCALAR_A)|(command==`COMMAND_OUTPUT_A)|(command==`COMMAND_LOAD_A)|(command==`COMMAND_STORE_CLEAR_A)|(command==`COMMAND_STORE_IDENT_A)|(command==`COMMAND_ADD_A))?n_row:n)
`define N_COL n_col

module matrixproc(din,dout,cs,rd,wr, dataORstatus, sysclk, reset, alua0, alub0, aluc0, alur2);
  input [15:0] din;
  output [15:0] dout;
  input cs,rd,wr,sysclk,reset;
  input dataORstatus;
  output [15:0] alua0, alub0, aluc0;
  input [15:0] alur2;
  //wire [15:0] din;
  //wire [15:0] dout;

  reg [15:0] datain,status;
  reg distrb,dostrb;

  always @(posedge sysclk)
    begin
      if (cs==0 && rd==1 && wr==0 && dataORstatus)
        begin
          datain <= din;
          distrb <= 1;
        end
      else
        begin
          distrb <= 0;
        end
    end

  reg[15:0] dataout;
  wire oe = ~cs & ~rd & wr;

  assign dout = dataORstatus ? dataout : status;

  always @(posedge sysclk)
    begin
      dostrb <= oe & dataORstatus;
    end



  reg[15:0] command;

  reg [15:0] alua0, alub0, aluc0;
  //wire [15:0] alur2;

  /*wire*/ reg [15:0] c_do,m_do;
	//wire [1:0]  c_dop,m_dop;
  reg [15:0] c_di,m_di;
  reg [15:0] c_addr,m_addr;
  reg c_we,m_we;
  reg c_en,m_en;

  //base address of matrix in memory
  reg [15:0] addr;

  //matrix size (assume square for the moment)
  reg [15:0] n;
  reg [15:0] n2;  //= n*n-1

  //matrix size (for ****rect)
  reg [15:0] n_row;
  reg [15:0] n_col;

  //indices (extra bit for overflow)
  reg [`BITS_MAXMAT:0] i,j,k,pivotrow;


  //internal matrix accumulator (result)
  reg [15:0] a[`MAXMAT*`MAXMAT-1:0];


  //scalar to multiply by
  reg [15:0] scalar;

  //LNS pipeline control
  reg [2*`BITS_MAXMAT-1:0] aluaddr0,aluaddr1,aluaddr2;
  reg aluvalid0,aluvalid1,aluvalid2;
  reg aluvalidc0,aluvalidc1,aluvalidc2;

  always
    begin
     @(posedge sysclk) `ENS;
        aluaddr1 <= @(posedge sysclk) 0;
        aluvalid1 <= @(posedge sysclk) 0;
        aluvalidc1 <= @(posedge sysclk) 0;
        aluaddr2 <= @(posedge sysclk) 0;
        aluvalid2 <= @(posedge sysclk) 0;
        aluvalidc2 <= @(posedge sysclk) 0;
     forever
     begin
     @(posedge sysclk) `ENS;
      if (aluvalid2)
        a[aluaddr2] <= `NCLK alur2;
//      if (aluvalidc2)
//        c[aluaddr2] <= `NCLK alur2;
      aluaddr2 <= @(posedge sysclk) aluaddr1;
      aluvalid2 <= @(posedge sysclk) aluvalid1;
      aluaddr1 <= @(posedge sysclk) aluaddr0;
      aluvalid1 <= @(posedge sysclk) aluvalid0;
      aluvalidc2 <= @(posedge sysclk) aluvalidc1;
      aluvalidc1 <= @(posedge sysclk) aluvalidc0;
     end
    end

  `ifdef DEBUG_EVERY_PIPE
    always @(posedge sysclk) #10
    begin
      if (aluvalid2 | aluvalid1 | aluvalid0 | aluvalidc2 | aluvalidc1 | aluvalidc0)
        begin
          $display("    addr=%d addr1=%d addr0=%d ",aluaddr2,aluaddr1,aluaddr0);
          $display("    v2=%b v1=%b v0=%b",aluvalid2,aluvalid1,aluvalid0);
          $display("    vc2=%b vc1=%b vc0=%b",aluvalidc2,aluvalidc1,aluvalidc0);
        end
    end
  `endif

  //start of arith functions

  function [15:0] lns_lt;
    input [15:0] x,y;
    begin
      lns_lt = {~x[15],~x[15]^x[14],x[13:0]} < {~y[15],~y[15]^y[14],y[13:0]};
    end
  endfunction


  function [15:0] lns_abs;
    input [15:0] x;
    reg [15:0] r;
    begin
      lns_abs = x[14:0];
    end
  endfunction

  function [15:0] mul2_comp;//for an input x this function calculates 1/x^2
    input [15:0] x;
    begin
      mul2_comp = (~(x[14:0] << 1))+1;
      mul2_comp[15]=1'b0;
    end
  endfunction

  function [15:0] mul3_comp;//for an input x this function calculates 1/x^3
    input [15:0] x;
    begin
      mul3_comp = {x[15],~(x[14:0]+((x[14:0] << 1)+15'b1))};
      mul3_comp[15]=x[15];
    end
  endfunction

  //end of arith functions

  always
    begin
        aluaddr0 <= @(posedge sysclk) 0;
        aluvalid0 <= @(posedge sysclk) 0;
        aluvalidc0 <= @(posedge sysclk) 0;
      @(posedge sysclk) `ENS;
      @(posedge sysclk) `ENS;
      @(posedge sysclk) `ENS;
        status <= @(posedge sysclk) `NORM_STATUS;
        dataout <= @(posedge sysclk) 0;
        n <= @(posedge sysclk) 2;
        i <= @(posedge sysclk) 0;
        j <= @(posedge sysclk) 0;
        k <= @(posedge sysclk) 0;
        c_en <= @(posedge sysclk) 0;
        c_we <= @(posedge sysclk) 0;
        m_en <= @(posedge sysclk) 0;
        m_we <= @(posedge sysclk) 0;
      @(posedge sysclk) `ENS;
       forever
        begin
            `STARTDI;
            command <= @(posedge sysclk) datain;
            `FINISHDI;
            `ifdef DEBUG_EVERY_COMMAND
               $display("command=%d time=%d",command,$time);
            `endif
          @(posedge sysclk) `ENS;
            if      (command == `COMMAND_RESET)
              begin  //reserved for reset operations
                scalar <= @(posedge sysclk) `INT_ONE;
                status <= @(posedge sysclk) `NORM_STATUS;
              end
            else if (command == `COMMAND_SET_N)
              begin  // input n (size of matrices) from host
                `STARTDI;
                n <= @(posedge sysclk) datain;
                //n_row <= @(posedge sysclk) datain;  //****rect
                //n_col<= @(posedge sysclk) datain;   //****rect
                n2 <= @(posedge sysclk) -1;
                `FINISHDI;
                while (i < n)
                  begin
                    i <= @(posedge sysclk) i + 1;
                    n2 <= @(posedge sysclk) n2 + n;
                   @(posedge sysclk) `ENS;
                  end
                i <= @(posedge sysclk) 0;
                `ifdef DEBUG_EVERY_DATA
                $display("n=%d n2=%d time=%d",n,n2,$time);
                `endif
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if (command == `COMMAND_SET_RC)          //****rect
              begin  // input n_row,n_col from host
                `STARTDI;
                n_row <= @(posedge sysclk) {8'h0,datain[15:8]};
                n_col <= @(posedge sysclk) {8'h0,datain[7:0]};
                n2 <= @(posedge sysclk) -1;
                `FINISHDI;
                while (i < n_row)
                  begin
                    i <= @(posedge sysclk) i + 1;
                    n2 <= @(posedge sysclk) n2 + n_col;
                   @(posedge sysclk) `ENS;
                  end                                       //is n2 supposed to be n_row*n_col?
                i <= @(posedge sysclk) 0;
                `ifdef DEBUG_EVERY_DATA
                $display("nr=%d nc=%d n2=%d time=%d",n_row,n_col,n2,$time);
                `endif
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if ((command == `COMMAND_GET_A) ||  //transfer a[i,j] to host
                     (command == `COMMAND_GET_C))    //transfer c[i,j] to host
              begin
                `STARTDI;
                i <= @(posedge sysclk) datain[15:8];
                j <= @(posedge sysclk) datain[7:0];
                k <= @(posedge sysclk) datain[7:0];
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                $display("get i=%d j=%d time=%d",i,j,$time);
                `endif
                if (command == `COMMAND_GET_A)
                  dataout <= @(posedge sysclk) a[`IJ];
//                else
//                  dataout <= @(posedge sysclk) c[`IK];
                `STARTDO;
                `FINISHDO;
                i <= @(posedge sysclk) 0;
                j <= @(posedge sysclk) 0;
                k <= @(posedge sysclk) 0;
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if (command == `COMMAND_GET_PIVOT)
              begin
                 dataout <= @(posedge sysclk) pivotrow;
                `STARTDO;
                `FINISHDO;
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if (command == `COMMAND_GET_X)
              begin
                 dataout <= @(posedge sysclk) scalar;
                `STARTDO;
                `FINISHDO;
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if (command == `COMMAND_PUT_X)
              begin
                `STARTDI;
                scalar <= @(posedge sysclk) datain;
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                  $display("put x=",convert.lnstoreal(scalar));
                `endif
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if (command == `COMMAND_PUT_PIVOT)
              begin
                `STARTDI;
                 pivotrow <= @(posedge sysclk) datain;
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                $display("put p=",pivotrow);
                `endif
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if ((command == `COMMAND_PUT_A) ||  //transfer a[i,j] from host
                     (command == `COMMAND_PUT_C))    //transfer c[i,j] from host
              begin
                `STARTDI;
                i <= @(posedge sysclk) datain[15:8];
                j <= @(posedge sysclk) datain[7:0];
                k <= @(posedge sysclk) datain[7:0];
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                $display("put i=%d j=%d time=%d",i,j,$time);
                `endif
                `STARTDI;
                if (command == `COMMAND_PUT_A)
                   a[`IJ] <= `NCLK datain;
//                else
//                   c[`IK] <= `NCLK datain;
                `FINISHDI;
                i <= @(posedge sysclk) 0;
                j <= @(posedge sysclk) 0;
                k <= @(posedge sysclk) 0;
                @(posedge sysclk) `ENS;  // to allow status to change at bottom of loop
              end
            else if ((command == `COMMAND_INPUT_C)  || // input c (right matrix operand) from host in row major order
                     (command == `COMMAND_OUTPUT_C) || // output c (right matrix operand) from host in row major order
                     (command == `COMMAND_OUTPUT_A) ||   // output a (matrix accumulator) from host in row major order
                     (command == `COMMAND_OUTPUT_M))
              begin
              	addr <= @(posedge sysclk) 0;
                //$display("NROW=",`N_ROW," NCOL=",`N_COL);
                while (i < `N_ROW)       // ****rect  n)
                  begin
                     while (j < `N_COL)  // ****rect  n)
                      begin
                        @(posedge sysclk) `ENS;
                           if (command == `COMMAND_INPUT_C)   //checked on FPGA
                             begin
                              `STARTDI;
															 c_we <= @(posedge sysclk) 1'b1;
															 c_en	<= @(posedge sysclk) 1'b1;
                               //c[`IK] <= `NCLK datain;
                               c_addr <= @(posedge sysclk) `IK;
                               c_di <= @(posedge sysclk) datain;
                               @(posedge sysclk) `ENS;
															 c_we <= @(posedge sysclk) 1'b0;
															 c_en	<= @(posedge sysclk) 1'b0;
															 //c_we <= `NCLK 1'b0;
															 //c_en	<= `NCLK 1'b0;
                               j <= @(posedge sysclk) j + 1;
                               k <= @(posedge sysclk) k + 1;
                               `FINISHDI;
                             end
                           else
                             begin
                               if (command == `COMMAND_OUTPUT_C)   //checked on FPGA
                               begin
													 	     c_we <= @(posedge sysclk)  1'b0;
														 	   c_en	<= @(posedge sysclk)  1'b1;
                                 c_addr <= @(posedge sysclk) `IK;
                                 @(posedge sysclk) `ENS;
                                 @(posedge sysclk) `ENS;
                                 @(posedge sysclk) `ENS;
                                 dataout <= @(posedge sysclk) c_do;
	  												 	   c_we <= @(posedge sysclk)  1'b0;
														 	   c_en	<= @(posedge sysclk)  1'b0;
                               end
                               else if (command == `COMMAND_OUTPUT_M)  //checked on FPGA
                               begin
													 	     m_we <= @(posedge sysclk)  1'b0;
														 	   m_en	<= @(posedge sysclk)  1'b1;
                                 m_addr <= @(posedge sysclk) addr;
                                 @(posedge sysclk) `ENS;
                                 @(posedge sysclk) `ENS;
                                 @(posedge sysclk) `ENS;
                                 dataout <= @(posedge sysclk) m_do;
	  												 	   m_we <= @(posedge sysclk)  1'b0;
														 	   m_en	<= @(posedge sysclk)  1'b0;
                               end
                               else
                                 dataout <= @(posedge sysclk) a[`IJ];// COMMAND_OUTPUT_A //checked on FPGA
                               j <= @(posedge sysclk) j + 1;
                               k <= @(posedge sysclk) k + 1;
                               addr <= @(posedge sysclk) addr + 1;
                               `STARTDO;
                        			 //$write(dataout," ");
                        			 //$write(databus," ");
                        			 //$write(testmatrix.databus," ");
                        			 //$write(" %b %b ",dostrb,oe,data_addr_sel);
                        			 //$write(" time=",$time);
                               `FINISHDO;
                             end
                        			 //$display(" ");
                      end
                      i <= @(posedge sysclk) i + 1;
                      j <= @(posedge sysclk) 0;
                      k <= @(posedge sysclk) 0;
                      @(posedge sysclk) `ENS;
                  end
                i <= @(posedge sysclk) 0;
              end
            else if ((command == `COMMAND_STORE_C)         ||// store c (right matrix operand) into memory
                     (command == `COMMAND_LOAD_C)          ||// load c (right matrix operand) from memory
                     (command == `COMMAND_LOAD_A)          ||// load a (matrix result) from memory
                     (command == `COMMAND_STORE_CLEAR_A)   ||// store a (matrix result) into memory and also clear a
                     (command == `COMMAND_STORE_IDENT_A)   ||// store a (matric result) into memory and also make a=ident
                     (command == `COMMAND_ADD_A)           ||// add matrix from memory to a (matrix accumulator)
                     (command == `COMMAND_MUL_SCALAR_A)    ||// multiply a with the scalar and store in a
                     (command == `COMMAND_ADD_SCALAR_A))      // add a matrix to a multiplied by a scalar A=A+xB
              begin
                `STARTDI;
                addr <= @(posedge sysclk) datain;
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                $display("load/store/add addr=%d time=%d",addr,$time);
                `endif
                while (i < `N_ROW)   // **** rect  n)
                  begin
                     while (j < `N_COL)  //   ****rect n)
                      begin
                          if (command == `COMMAND_STORE_C)         //checked on FPGA
                          	begin
													 		c_we <= @(posedge sysclk)  1'b0;
													 		c_en <= @(posedge sysclk)  1'b1;
                              c_addr <= @(posedge sysclk)  `IK;
                              m_addr <= @(posedge sysclk)  addr;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
															m_di <= @(posedge sysclk)  c_do;
															m_we <= @(posedge sysclk)  1'b1;
															m_en <= @(posedge sysclk)  1'b1;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
													 		c_we <= @(posedge sysclk)  1'b0;
													 		c_en <= @(posedge sysclk)  1'b0;
															m_we <= @(posedge sysclk)  1'b0;
															m_en <= @(posedge sysclk)  1'b0;
                          	end
                          if ((command == `COMMAND_LOAD_C))       //checked on FPGA
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b1;
                              m_addr <= @(posedge sysclk)  addr;
                              c_addr <= @(posedge sysclk)  `IK;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
															c_di <= @(posedge sysclk)  m_do;
															c_we <= @(posedge sysclk)  1'b1;
															c_en <= @(posedge sysclk)  1'b1;
                              @(posedge sysclk) `ENS;
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b0;
															c_we <= @(posedge sysclk)  1'b0;
															c_en <= @(posedge sysclk)  1'b0;
                              //c[`IK] <= `NCLK m[addr];
                          if (command == `COMMAND_LOAD_A)          //checked on FPGA
                          	begin
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b1;
                              m_addr <= @(posedge sysclk)  addr;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              a[`IJ] <= @(posedge sysclk) m_do;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b0;
                            end
                          if ((command == `COMMAND_STORE_CLEAR_A)||  //checked on FPGA
                              (command == `COMMAND_STORE_IDENT_A))   //checked on FPGA
                             begin
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
  														 m_di <= @(posedge sysclk)  a[`IJ];
	  													 m_we <= @(posedge sysclk)  1'b1;
		  												 m_en <= @(posedge sysclk)  1'b1;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
			 		 				  					 m_we <= @(posedge sysclk)  1'b0;
				  										 m_en <= @(posedge sysclk)  1'b0;
                               //m[addr] <= `NCLK a[`IJ];
                               if ((command == `COMMAND_STORE_IDENT_A) && (i == j))  //checked on FPGA
                                 begin
                                  //a[`IJ] <= `NCLK `INT_ONE;//`INT_ONE can be replaced with the value that I is multiplied with in Hess
   		                            @(posedge sysclk) `ENS;//for a reason this delay may affect the ADD_A command
                                   a[`IJ] <= @(posedge sysclk) `INT_ONE;//`INT_ONE can be replaced with the value that I is multiplied with in Hessian
   		                            @(posedge sysclk) `ENS;
   		                           end
                               else
                               	 begin
                                  //a[`IJ] <= `NCLK `INT_ZERO;
                                  @(posedge sysclk) `ENS;//for a reason this delay may affect the ADD_A command
                                  a[`IJ] <= @(posedge sysclk) `INT_ZERO;
                                  @(posedge sysclk) `ENS;
                                end
                             end
                           if (command == `COMMAND_ADD_A)            //checked on FPGA
                             begin                                   //but if I remove the first delays in the two previous
													 		 m_we <= @(posedge sysclk)  1'b0;      //if statements (7 and 14 lines above this line) the
													 		 m_en <= @(posedge sysclk)  1'b1;      //ADD_A command doesn't work!!!! I don't know why
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               aluvalid0 <= @(posedge sysclk) 1;
                               aluaddr0 <= @(posedge sysclk) `IJ;
                               alua0 <= @(posedge sysclk) a[`IJ];
                               alub0 <= @(posedge sysclk)  m_do;
                               aluc0  <= @(posedge sysclk) `INT_ONE;
                               @(posedge sysclk) `ENS;     //I checked if it works with 1 delay in this position and it doesn't
                               @(posedge sysclk) `ENS;
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b0;
                             end
                           if (command == `COMMAND_ADD_SCALAR_A)   //A=A+xB
                             begin
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b1;
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               aluvalid0 <= @(posedge sysclk) 1;
                               aluaddr0 <= @(posedge sysclk) `IJ;
                               alua0 <= @(posedge sysclk) a[`IJ];
                               alub0 <= @(posedge sysclk)  m_do;
                               aluc0  <= @(posedge sysclk) scalar;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b0;
                             end
                          if (command == `COMMAND_MUL_SCALAR_A)  //checked on FPGA
                             begin                               //A=xA
                               aluvalid0 <= @(posedge sysclk) 1;
                               aluaddr0 <= @(posedge sysclk) `IJ;
                               alua0 <= @(posedge sysclk) `INT_ZERO;
                               alub0 <= @(posedge sysclk)  datain;
                               aluc0  <= @(posedge sysclk) a[`IJ];
                               @(posedge sysclk) `ENS;
                             end
                          j <= @(posedge sysclk) j + 1;
                          k <= @(posedge sysclk) k + 1;
                          addr <= @(posedge sysclk) addr + 1;
                        @(posedge sysclk) `ENS;
                      end
                     aluvalid0 <= @(posedge sysclk) 0;
                     i <= @(posedge sysclk) i + 1;
                     j <= @(posedge sysclk) 0;
                     k <= @(posedge sysclk) 0;
                    @(posedge sysclk) `ENS;
                  end
                i <= @(posedge sysclk) 0;
              end
            else if (command == `COMMAND_MULVEC_CR_RECT)                          //checked on FPGA
              begin  // multiply vector from memory by matrix c (right op)
                     // with vector result added to a (matrix accumulator)
                `STARTDI;
                addr <= @(posedge sysclk) datain;
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                $display("mulvec c addr=%d time=%d",addr,$time);
                `endif
                     while (k < n)
                      begin
                        while (j < n_row)
                          begin
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b1;
													 		 c_we <= @(posedge sysclk)  1'b0;
													 		 c_en <= @(posedge sysclk)  1'b1;
                               m_addr <= @(posedge sysclk)  addr+k;
                               c_addr <= @(posedge sysclk)  `JK;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               aluvalid0 <= @(posedge sysclk) 1;
                               aluaddr0 <= @(posedge sysclk) `IJ;
                               alua0 <= @(posedge sysclk) a[`IJ];
                               alub0 <= @(posedge sysclk)  m_do;
                               aluc0  <= @(posedge sysclk) c_do;
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b0;
													 		 c_we <= @(posedge sysclk)  1'b0;
													 		 c_en <= @(posedge sysclk)  1'b0;
                               //a[`IJ] <= `NCLK int_add(a[`IJ], int_mul(m[addr+k], c[`KJ]));
                               j <= @(posedge sysclk) j + 1;
                            @(posedge sysclk) `ENS;
                          end
                        aluvalid0 <= @(posedge sysclk) 0;
                        k <= @(posedge sysclk) k + 1;
                        j <= @(posedge sysclk) 0;
                        if (n_row==2)
                          begin
                            @(posedge sysclk) `ENS;  //extra delay for pipeline
                          end
                       @(posedge sysclk) `ENS;
                      end
                     k <= @(posedge sysclk) 0;                /*new order*/
              end
            else if ((command == `COMMAND_STORE_CLEAR_VECA)|| // store a (vector result) into memory and also clear a
                     (command == `COMMAND_ADDVEC_A)        || // add matrix from memory to a (matrix accumulator)
                     (command == `COMMAND_STORE_ROWA)      ||
                     (command == `COMMAND_STORE_ROWC)      ||
                     (command == `COMMAND_LOAD_ROWA)       ||
                     (command == `COMMAND_LOAD_ROWC)       ||
                     (command == `COMMAND_ADDSCALVEC_A)    ||
                     (command == `COMMAND_ADDSCALVEC_C)    ||
                     (command == `COMMAND_MUL2_COMP)       ||
                     (command == `COMMAND_MUL3_COMP)       ||
                     (command == `COMMAND_SUM_A))
              begin
                `STARTDI;
                addr <= @(posedge sysclk) datain;
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                $display("veca addr=%d time=%d",addr,$time);
                `endif
                if ((command == `COMMAND_STORE_ROWA)   ||
                    (command == `COMMAND_STORE_ROWC)   ||
                    (command == `COMMAND_LOAD_ROWA)    ||
                    (command == `COMMAND_LOAD_ROWC)    ||
                    (command == `COMMAND_ADDSCALVEC_A) ||
                    (command == `COMMAND_ADDVEC_A)     ||
                    (command == `COMMAND_ADDSCALVEC_C))
                  begin
                    `STARTDI;
                    if (datain == n)
                      begin
                        i <= @(posedge sysclk) pivotrow;
                        k <= @(posedge sysclk) pivotrow;
                      end
                    else
                      begin
                        i <= @(posedge sysclk) datain;
                        k <= @(posedge sysclk) datain;
                      end
                    `FINISHDI;
                    `ifdef DEBUG_EVERY_DATA
                    $display("row=%d time=%d",i,$time);
                    `endif
                  end
                     while (j < n)
                      begin
                          if (command == `COMMAND_STORE_CLEAR_VECA)  //checked on FPGA
                             begin
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
  														 m_di <= @(posedge sysclk)  a[`IJ];
                               //a[`IJ] <= `NCLK `INT_ZERO;
                               a[`IJ] <= @(posedge sysclk) `INT_ZERO;
	  													 m_we <= @(posedge sysclk)  1'b1;
		  												 m_en <= @(posedge sysclk)  1'b1;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
			 		 				  					 m_we <= @(posedge sysclk)  1'b0;
				  										 m_en <= @(posedge sysclk)  1'b0;
                            end
                          if (command == `COMMAND_SUM_A)             //checked on FPGA
                             begin
													 		 m_we <= @(posedge sysclk)  1'b0;       //after this command scalar holds the sum
													 		 m_en <= @(posedge sysclk)  1'b1;
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               aluvalid0 <= @(posedge sysclk) 1;
                               aluaddr0 <= @(posedge sysclk) 16'b0;
                               alua0 <= @(posedge sysclk) a[16'b0];
                               alub0 <= @(posedge sysclk)  m_do;
                               aluc0  <= @(posedge sysclk) `INT_ONE;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b0;
                             end
                          if (command == `COMMAND_ADDVEC_A)             //checked on FPGA
                             begin
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b1;
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               aluvalid0 <= @(posedge sysclk) 1;
                               aluaddr0 <= @(posedge sysclk) `IJ;
                               alua0 <= @(posedge sysclk) a[`IJ];
                               alub0 <= @(posedge sysclk)  m_do;
                               aluc0  <= @(posedge sysclk) `INT_ONE;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b0;
                            end
                          if (command == `COMMAND_ADDSCALVEC_A)             //checked on FPGA
                            begin                                           //A=A+xB
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b1;
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
                               aluvalid0 <= @(posedge sysclk) 1;
                               aluaddr0 <= @(posedge sysclk) `IJ;
                               alua0 <= @(posedge sysclk) a[`IJ];
                               alub0 <= @(posedge sysclk)  m_do;
                               aluc0  <= @(posedge sysclk) scalar;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
													 		 m_we <= @(posedge sysclk)  1'b0;
													 		 m_en <= @(posedge sysclk)  1'b0;
                            end
                          if (command == `COMMAND_STORE_ROWA)             //checked on FPGA
                            begin
                               m_addr <= @(posedge sysclk)  addr;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
  														 m_di <= @(posedge sysclk)  a[`IJ];
                               //a[`IJ] <= `NCLK `INT_ZERO;
	  													 m_we <= @(posedge sysclk)  1'b1;
		  												 m_en <= @(posedge sysclk)  1'b1;
                               @(posedge sysclk) `ENS;
                               @(posedge sysclk) `ENS;
			 		 				  					 m_we <= @(posedge sysclk)  1'b0;
				  										 m_en <= @(posedge sysclk)  1'b0;
                            end
                          if (command == `COMMAND_LOAD_ROWA)             //checked on FPGA
                            begin
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b1;
                              m_addr <= @(posedge sysclk)  addr;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              a[`IJ] <= @(posedge sysclk) m_do;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b0;
                            end
                          if (command == `COMMAND_MUL2_COMP)             //checked on FPGA
                            begin
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b1;
                              m_addr <= @(posedge sysclk)  addr;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              a[`IJ] <= @(posedge sysclk) mul2_comp(m_do);
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b0;
															//a[`IJ] <= mul2_comp(m[addr]);
                            end
                           if (command == `COMMAND_MUL3_COMP)             //checked on FPGA
                            begin
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b1;
                              m_addr <= @(posedge sysclk)  addr;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              a[`IJ] <= @(posedge sysclk) mul3_comp(m_do);
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
                              @(posedge sysclk) `ENS;
													 		m_we <= @(posedge sysclk)  1'b0;
													 		m_en <= @(posedge sysclk)  1'b0;
													 		//a[`IJ] <= mul3_comp(m[addr]);
                            end
                          j <= @(posedge sysclk) j + 1;
                          addr <= @(posedge sysclk) addr + 1;
                        @(posedge sysclk) `ENS;
                      end
                     aluvalid0 <= @(posedge sysclk) 0;
                     aluvalidc0 <= @(posedge sysclk) 0;
 										 if ((command == `COMMAND_SUM_A) && (j==n))             //checked on FPGA
										 begin
                       @(posedge sysclk) `ENS;
										 	 scalar <= @(posedge sysclk) a[16'b0];
										 end
                     i <= @(posedge sysclk) 0;
                     j <= @(posedge sysclk) 0;
                     k <= @(posedge sysclk) 0;
              end
            else if (command == `COMMAND_FIND_PIVOT)             //checked on FPGA
              begin
                scalar <= @(posedge sysclk) `INT_ZERO;
                pivotrow <= @(posedge sysclk) n;
                `STARTDI;
                i <= @(posedge sysclk) datain[15:8];
                k <= @(posedge sysclk) datain[7:0];
                `FINISHDI;
                `ifdef DEBUG_EVERY_DATA
                $display("find i=%d k=%d time=%d",i,k,$time);
                `endif
                while (i < n)
                  begin
    								 	 c_we <= @(posedge sysclk)  1'b0;
		  							 	 c_en <= @(posedge sysclk)  1'b1;
                       c_addr <= @(posedge sysclk)  `IK;
                       @(posedge sysclk) `ENS;
                       @(posedge sysclk) `ENS;
                       if (lns_lt(lns_abs(scalar), lns_abs(c_do)))
                         begin
													 scalar <= @(posedge sysclk) c_do;
                           //scalar <= @(posedge sysclk) c[`IK];
                           pivotrow <= @(posedge sysclk) i;
                         end
  							 		   c_we <= @(posedge sysclk)  1'b0;
    							 	   c_en <= @(posedge sysclk)  1'b0;
                       i <= @(posedge sysclk) i + 1;
                       @(posedge sysclk) `ENS;
                  end
                i <= @(posedge sysclk) 0;
                k <= @(posedge sysclk) 0;
              end

            status <= @(posedge sysclk) `NORM_STATUS;
        end
    end

`ifdef DEBUG_EVERY_CLOCK
   always @(posedge sysclk) #1
    $display("status=%b datain=%d dataout=%d dost=%b i=%d j=%d k=%d ad=%d $time=%d",status,datain,dataout,dostrb,i,j,k,addr,$time);
`endif

//`include "SRAMs.v"
`include "mySRAMs.v"

//`include "yuyumatrixdata.v"


endmodule





