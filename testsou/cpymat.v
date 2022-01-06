`include "concore.v"

module cpymat;
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
            concore.readdata(1,"ym",init_simtime_ym);
          end
        ym = concore.data[0]; 
        u = ym + 1.0;
        concore.data[0] = u;
        $display("ym=",ym," u=",u);
        concore.writedata(1,"u",0);
      end 
    concore.write(1,"u",init_simtime_u);
    $display("retry=",concore.retrycount);
  end
endmodule
