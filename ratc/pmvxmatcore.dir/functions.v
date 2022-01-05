//following tasks are part of "wrapper"
  task initialize_wrapper;
    begin
         cs = 1;
         rd = 1;
         wr = 1;
         dataORstatus = 0;
    end
  endtask

  task send_data;
    input [15:0] dat;
    begin
      #`PROCESSOR_DELAY cs = 0; rd = 1; wr = 0; dataORstatus = 1;
      din = dat;
      #`PROCESSOR_DELAY cs = 1; rd = 1; wr = 1;
    end
  endtask

  task send_command;
    input [15:0] cmd;
    begin
      send_data(cmd);
    end
  endtask


  task rcv_data;
    output [15:0] dat;
    begin
      #`PROCESSOR_DELAY cs = 0; rd = 0; wr = 1; dataORstatus = 1;
#51 //$display("dat=",databus," time=",$time);
      dat = dout;
      #`PROCESSOR_DELAY cs = 1; rd = 1; wr = 1;
    end
  endtask

  task rcv_status;
    output [15:0] stat;
    begin
      #`PROCESSOR_DELAY cs = 0; rd = 0; wr = 1; dataORstatus = 0;
#51      stat = dout;
      #`PROCESSOR_DELAY cs = 1; rd = 1; wr = 1;
    end
  endtask
//end of "wrapper" tasks



  task wait_status;
    reg [15:0] stat;
    begin
      rcv_status(stat);
      while (stat&`BUSY_MASK_STATUS)
        rcv_status(stat);
    end
  endtask


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
//functionss that convert from internal representation ("int") to verilog real
//in this case, the internal representation is simply unsigned integer

  function real int2real;
    input [15:0] x;

    begin
      int2real = lnstoreal(x);
    end
  endfunction

  function [15:0] real2int;
    input x;
    real x;

    begin
    real2int = realtolns(x);
    end
  endfunction




  reg[15:0] mat[`MAXMAT*`MAXMAT-1:0];

  task rcv_mat;
    input [15:0] nn;
    integer ii,jj;
    integer temp;

    reg [`BITS_MAXMAT-1:0] ireg,jreg;

    begin
      for (ii=0; ii<nn; ii=ii+1)
        for (jj=0; jj<nn; jj=jj+1)
          begin
            ireg = ii;
            jreg = jj;
            rcv_data(temp);
            mat[{ireg,jreg}] = temp;
          end
    end
  endtask


  task print_mat;
    input [15:0] nn;

    integer ii,jj;
    reg [`BITS_MAXMAT-1:0] ireg,jreg;

    begin
      for (ii=0; ii<nn; ii=ii+1)
       begin
        for (jj = 0; jj<nn; jj=jj+1)
          begin
            ireg = ii;
            jreg = jj;
            $write(int2real(mat[{ireg,jreg}])," ");
//            $write("(",mat[{ireg,jreg}],")");
          end
        $display(" ");
       end
    end
  endtask

  task rcv_matrect;
    input [15:0] nr,nc;
    integer ii,jj;
    integer temp;

    reg [`BITS_MAXMAT-1:0] ireg,jreg;

    begin
      for (ii=0; ii<nr; ii=ii+1)
        for (jj=0; jj<nc; jj=jj+1)
          begin
            ireg = ii;
            jreg = jj;
            rcv_data(temp);
            mat[{ireg,jreg}] = temp;
          end
    end
  endtask


  task print_matrect_hex;
    input [15:0] nr,nc;

    integer ii,jj;
    reg [`BITS_MAXMAT-1:0] ireg,jreg;

    begin
      for (ii=0; ii<nr; ii=ii+1)
       begin
        for (jj = 0; jj<nc; jj=jj+1)
          begin
            ireg = ii;
            jreg = jj;
            //$write(int2real(mat[{ireg,jreg}])," ");
            //$write(mat[{ireg,jreg}]," ");
            $write("%h ",mat[{ireg,jreg}]);
//            $write("(",mat[{ireg,jreg}],")");
          end
        $display(" ");
       end
    end
  endtask

  task print_matrect;
    input [15:0] nr,nc;

    integer ii,jj;
    reg [`BITS_MAXMAT-1:0] ireg,jreg;

    begin
      for (ii=0; ii<nr; ii=ii+1)
       begin
        for (jj = 0; jj<nc; jj=jj+1)
          begin
            ireg = ii;
            jreg = jj;
            $write(int2real(mat[{ireg,jreg}])," ");
//            $write("(",mat[{ireg,jreg}],")");
          end
        $display(" ");
       end
    end
  endtask