`define MAXLEN 25
module cpymat;
  integer f,fout;
  integer lens=0;
  reg[`MAXLEN*8-1:0] s=0;
  integer i;
  real dummy;
  initial
   begin
     $display("cpymat.v");
     readhelper;
   end

  always @(lens or s)
   begin
     writehelper;
     $display("w s=%s t=%d",s,$time/100.0);
     #0 readhelper;
     /*
     while (lens==0)
       begin
         $display("empty");
         #0 readhelper;
       end
     #0 readhelper;
     */
     $display("r s=%s t=%d",s,$time/100.0);
     //$display(lens);
     //$display("time=",$time);
     //$display("raw=%x",s);
     //$display("s=%s",s);
    end 

  function integer msbhelper;
    input [`MAXLEN*8-1:0] s;
    integer i,msb;
    begin
      //$display("help %s",s);
      msb = 7; 
      for (i=8; i<`MAXLEN*8; i=i+1)
        begin
          if (s[i]) msb = i;
        end 
      msbhelper = msb;
    end
  endfunction

  task writehelper;
    integer msb;
    begin
     fout = $fopen("./out1/u","w");
     msb = msbhelper(s);
     //$display("%s",s);
     //$display(msb);
     //$display(msb/8);
     //$display(`MAXLEN - msb/8 -1);
     $fdisplay(fout,"%s",s << (8*(`MAXLEN - msb/8 -1)));
     $fclose(fout);
    end
  endtask

  task readhelper;
    begin
     f = $fopen("./in1/ym","r");
     if (f==0)
     begin
       lens = 7;
       s  = "[0,0,0]";
     end
     else
     begin
       lens = $fgets(s,f);
       $fclose(f);
     end
    end
  endtask

  task delayhelper;
   begin
    dummy = 1.0;
    for (i=1; i<=20000; i=i+1)
     begin
	   dummy=dummy**0.99;
     end
   end
  endtask

  always #1
  begin
    delayhelper;
    if ($time> 10000) $finish;
    else if ($time % 6000 == 0) $display("time=",$time/100.0); 
    readhelper;
  end
endmodule

