`timescale 1ns/100ps

module matrixLNSproc(din,dout,cs,rd,wr, dataORstatus, sysclk, reset);
	input [15:0] din;
	output [15:0] dout;
	input cs,rd,wr,sysclk,reset;
  input dataORstatus;
  //wire [15:0] din;
  //wire [15:0] dout;

  wire [15:0] alua0, alub0, aluc0;
  wire [15:0] alur2;

  matrixproc matrixproc_inst(
  													.din(din),
  													.dout(dout),
  													.cs(cs),
  													.rd(rd),
  													.wr(wr),
  													.dataORstatus(dataORstatus),
  													.sysclk(sysclk),
  													.reset(reset),
  													.alua0(alua0),
  													.alub0(alub0),
  													.aluc0(aluc0),
  													.alur2(alur2)
  													);



  lnspipe lnspipe_inst(
  										.sysclk(sysclk),
  										.alua0(alua0),
  										.alub0(alub0),
  										.aluc0(aluc0),
  										.alur2(alur2)
  										);
endmodule