`include "concore.v"

// readdata keeps state for at most MAXFILES reads per step. Reading more
// than that must stop with "too many reads in loop" instead of hanging.
// run from a directory that has an empty in1/ folder
module test_read_limit;
reg [8*10-1:0] init = "[0.0, 1.0]";
integer k;

initial begin
  for (k = 0; k < `MAXFILES; k = k + 1) begin
    concore.readdata(1, "missing", init);
    if (concore.data[0] != 1.0) $fatal(1, "read %0d: data[0] is %f, expected 1.0", k + 1, concore.data[0]);
  end
  $display("%0d reads in one step ok", `MAXFILES);

  // this one is over the limit, readdata should call $finish itself
  concore.readdata(1, "missing", init);
  $fatal(1, "read %0d went past the MAXFILES limit", `MAXFILES + 1);
end
endmodule
