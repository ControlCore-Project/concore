`define CONCORE_MAXLEN 150 
`define INPATHLEN 6   //includes trailing portdigit and "/"
`define OUTPATHLEN 7  //modify these to match inpath and outpath
`define MAXFILES 9
module concore;
  integer   datasize;
  real      data[9:0];
  integer   filenum=-1;
  reg[`CONCORE_MAXLEN*8-1:0] curs;
  reg[`CONCORE_MAXLEN*8-1:0] s[`MAXFILES-1:0];
  reg[`CONCORE_MAXLEN*8-1:0] olds[`MAXFILES-1:0];
  integer lens[`MAXFILES-1:0];
  integer oldlens[`MAXFILES-1:0];
  reg[(`INPATHLEN-2)*8-1:0] inpath =  "./in"; //omits trailing portdigit and "/"
  reg[(`OUTPATHLEN-2)*8-1:0] outpath = "./out";
  real simtime;
  integer retrycount = 0;

  integer fin,fout;
  integer i;
  real dummy;

  integer iii;
  initial
   begin
    for(iii=0; iii<`MAXFILES; iii = iii+1)
    begin
     s[iii] = 0;
     olds[iii] = 0;
     lens[iii] = 0;
     oldlens[iii] = 0;
    end
  end

  function [0:0] unchanged;
    input [0:0] dummy_arg;
    reg nochange;
    begin
      nochange = 1;
      for (i=0; i<=filenum; i=i+1)
        begin
//$display("1oldl=%d l=%d olds=%s s=%s",oldlens[i],lens[i],olds[i],s[i]);
          if (!((oldlens[i] == lens[i])&&(olds[i] == s[i])))
            nochange = 0;
        end
      if (nochange) 
        begin
         for (i=0; i<=filenum; i=i+1)
           s[i] = 0;
         for (i=0; i<=filenum; i=i+1)
           lens[i] = 0;
         unchanged = 1;
         filenum = -1;
//$display("unchanged");
       end
     else
       begin
//         for (i=0; i<=filenum; i=i+1)
//$display("2oldl=%d l=%d olds=%s s=%s",oldlens[i],lens[i],olds[i],s[i]);
         for (i=0; i<=filenum; i=i+1)
           olds[i] = s[i];
         for (i=0; i<=filenum; i=i+1)
           oldlens[i] = lens[i];
         unchanged = 0;
//$display("changed");
      end
//         for (i=0; i<=filenum; i=i+1)
//$display("3oldl=%d l=%d olds=%s s=%s",oldlens[i],lens[i],olds[i],s[i]);
//$stop;
//     filenum = -1;
    end
  endfunction

  function integer msbhelper;
    input [`CONCORE_MAXLEN*8-1:0] s;
    integer i,msb;
    begin
      //$display("help %s",s);
      msb = 7; 
      for (i=8; i<`CONCORE_MAXLEN*8; i=i+1)
        begin
          if (s[i]) msb = i;
        end 
      msbhelper = msb;
    end
  endfunction

  function integer lsbhelper;
    input [`CONCORE_MAXLEN*8-1:0] s;
    integer i,lsb;
    begin
      //$display("help %s",s);
      lsb = 7; 
      for (i=`CONCORE_MAXLEN*8; i>=8; i=i-1)
        begin
          if (s[i]) lsb = i;
        end 
      lsbhelper = lsb;
    end
  endfunction

  function [`CONCORE_MAXLEN*8-1:0] trim;
   input [`CONCORE_MAXLEN*8-1:0] s;
   integer msb;
   begin 
     msb = msbhelper(s);
     //$display("%s",s);
     //$display(msb);
     //$display(msb/8);
     //$display(`CONCORE_MAXLEN - msb/8 -1);
     trim = s << (8*(`CONCORE_MAXLEN - msb/8 -1));
   end
  endfunction

  function integer len;
   input [`CONCORE_MAXLEN*8-1:0] s;
   integer msb;
   begin 
     msb = msbhelper(s);
     len = (msb/8)+1;
   end
  endfunction

  task readdata;  //passed via global data and datasize (from literal_eval)
    input integer port;
    input [`CONCORE_MAXLEN*8-1:0] name;
    input [`CONCORE_MAXLEN*8-1:0] initstr;
    reg datavalid;
    reg [(`CONCORE_MAXLEN+`INPATHLEN)*8-1:0] fname; //room for 6 extra chars
    reg [7:0] asciiport;
    integer i;
    begin
     filenum = filenum + 1;
     if (filenum > `MAXFILES)
       begin
         $display("too many reads in loop");
         $finish;
       end
     s[filenum] = 0;
     //olds[filenum] = 0;
     lens[filenum] = 0;
     //oldlens[filenum] = 0;
     asciiport = "0";
     asciiport = asciiport + port;
     fname = {inpath,asciiport,"/",trim(name)};
    datavalid = 0;
    while(datavalid == 0)
    begin
     delayhelper;
     //fin = $fopen(fname,"r");
     //fin = $fopen("./in1/ym","r");
     case (len(name))
       1: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-1)*8],"r");
       2: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-2)*8],"r");
       3: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-3)*8],"r");
       4: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-4)*8],"r");
       5: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-5)*8],"r");
       6: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-6)*8],"r");
       7: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-7)*8],"r");
       8: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-8)*8],"r");
       9: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-9)*8],"r");
      10: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-10)*8],"r");
      11: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-11)*8],"r");
      12: fin = $fopen( 
          fname[(`CONCORE_MAXLEN+`INPATHLEN)*8-1:(`CONCORE_MAXLEN-12)*8],"r");
      default: begin $display("filename too long:%s",name);$finish; end
     endcase
     datavalid = 0;
     if (fin==0)
     begin
       lens[filenum] = 7;//actual len?
       s[filenum]  = trim(initstr); //"[0,0,0]";
     end
     else
     begin
       lens[filenum] = $fgets(curs,fin);
       s[filenum] = curs;
       $fclose(fin);
     end
    //parse
    literal_eval(datavalid,simtime);
    if (datavalid == 0)
      begin
        retrycount = retrycount + 1;
      end
    //time
   end //datavalid
    end
  endtask

  task write;  //string argument only
    input integer port;
    input [`CONCORE_MAXLEN*8-1:0] name;
    input [`CONCORE_MAXLEN*8-1:0] val;
    reg [(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:0] fname;
    reg [7:0] asciiport;
    begin
     asciiport = "0";
     asciiport = asciiport + port;
     fname = {outpath,asciiport,"/",trim(name)};
     //$display("outfile=%s",fname);
     delayhelper;
     //fout = $fopen("./out1/u","w");
     //fout = $fopen(fname,"w");
     case (len(name))
       1: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-1)*8],"w");
       2: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-2)*8],"w");
       3: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-3)*8],"w");
       4: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-4)*8],"w");
       5: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-5)*8],"w");
       6: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-6)*8],"w");
       7: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-7)*8],"w");
       8: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-8)*8],"w");
       9: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-9)*8],"w");
      10: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-10)*8],"w");
      11: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-11)*8],"w");
      12: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-12)*8],"w");
      default: begin $display("filename too long:%s",name);$finish; end
     endcase
     $fdisplay(fout,"%s",trim(val));
     $fclose(fout);
    end
  endtask

  task writedata;  //passed via global data and datasize
    input integer port;
    input [`CONCORE_MAXLEN*8-1:0] name;
    input real delta;
    reg [(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:0] fname; //room for 7 extra chars
    reg [7:0] asciiport;
    integer i;
    real realdata;
    begin
     asciiport = "0";
     asciiport = asciiport + port;
     fname = {outpath,asciiport,"/",trim(name)};
     //$display("outfile=%s",fname);
     delayhelper;
     //fout = $fopen("./out1/u","w");
     //fout = $fopen(fname,"w");
     case (len(name))
       1: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-1)*8],"w");
       2: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-2)*8],"w");
       3: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-3)*8],"w");
       4: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-4)*8],"w");
       5: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-5)*8],"w");
       6: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-6)*8],"w");
       7: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-7)*8],"w");
       8: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-8)*8],"w");
       9: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-9)*8],"w");
      10: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-10)*8],"w");
      11: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-11)*8],"w");
      12: fout = $fopen( 
          fname[(`CONCORE_MAXLEN+`OUTPATHLEN)*8-1:(`CONCORE_MAXLEN-12)*8],"w");
      default: begin $display("filename too long:%s",name);$finish; end
     endcase
     $fwrite(fout,"[%g",simtime+delta);
     for (i=0; i<datasize; i=i+1)
       begin
         realdata = data[i];
         $fwrite(fout,",%g",realdata);
      end
     $fdisplay(fout,"]");
     $fclose(fout);
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

  task literal_eval;
   output valid;
   output real simtime;
   reg [7:0] lb;
   real      x0,x1,x2,x3,x4,x5,x6,x7,x8,x9;
   reg [7:0] c00,c01,c02,c03,c04,c05,c06,c07,c08,c09;

   begin
    curs = s[filenum];
    datasize =$sscanf(curs,"%c%e%c%e%c%e%c%e%c%e%c%e%c%e%c%e%c%e%c%e%c",lb,x0,c00,
    x1,c01,x2,c02,x3,c03,x4,c04,x5,c05,x6,c06,x7,c07,x8,c08,x9,c09)/2; 
    valid = 0;
    case(datasize)
       2: valid = {lb,c00,c01}                                =="[,]";
       3: valid = {lb,c00,c01,c02}                            =="[,,]";
       4: valid = {lb,c00,c01,c02,c03}                        =="[,,,]";
       5: valid = {lb,c00,c01,c02,c03,c04}                    =="[,,,,]";
       6: valid = {lb,c00,c01,c02,c03,c04,c05}                =="[,,,,,]";
       7: valid = {lb,c00,c01,c02,c03,c04,c05,c06}            =="[,,,,,,]";
       8: valid = {lb,c00,c01,c02,c03,c04,c05,c06,c07}        =="[,,,,,,,]";
       9: valid = {lb,c00,c01,c02,c03,c04,c05,c06,c07,c08}    =="[,,,,,,,,]";
      10: valid = {lb,c00,c01,c02,c03,c04,c05,c06,c07,c08,c09}=="[,,,,,,,,,]";
    endcase
    //data does not include not simtime
    simtime = x0;
    data[0] = x1;
    data[1] = x2;
    data[2] = x3;
    data[3] = x4;
    data[4] = x5;
    data[5] = x6;
    data[6] = x7;
    data[7] = x8;
    data[8] = x9;
    datasize = datasize - 1; 
   end
  endtask
endmodule

