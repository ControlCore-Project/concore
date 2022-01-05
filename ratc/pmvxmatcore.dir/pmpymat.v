`include "concore.v"

module pmpymat;
//concore.delay = 0.01
integer Nsim = 100;
reg [8*13-1:0] init_simtime_u = "[0.0,0.0,0.0]";
reg [8*13-1:0] init_simtime_ym = "[0.0,0.0,0.0]";
real ym; //only one element of data for this toy example
real u;

initial
  begin
    while(concore.simtime<Nsim)
      begin
        while (concore.unchanged(0))
          begin
            concore.readdata(1,"u",init_simtime_u);
          end
        u = concore.data[0]; 
        ym = u + 10000.0;
        concore.data[0] = ym;
        $display("ym=",ym," u=",u);
        concore.writedata(1,"ym",1);
      end 
    concore.write(1,"ym",init_simtime_ym);
    $display("retry=",concore.retrycount);
  end
endmodule
