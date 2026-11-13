`include "concore.v"

// read_file cases from tests/protocol_fixtures/python_phase1_cases.json
// run from a directory that has an empty in1/ folder
module test_read_simtime;
reg [8*10-1:0] missing_init = "[0.0, 5.0]";
reg [8*10-1:0] ym_init = "[0.0, 0.0]";
integer f;

initial begin
  // read_file/missing_file_returns_default_and_false
  concore.simtime = 4;
  concore.readdata(1, "missing", missing_init);
  if (concore.simtime != 4) $fatal(1, "missing file: simtime is %f, expected 4", concore.simtime);
  if (concore.data[0] != 5.0) $fatal(1, "missing file: data[0] is %f, expected 5.0", concore.data[0]);

  // read_file/older_timestamp_does_not_decrease_simtime
  f = $fopen("in1/ym", "w");
  $fwrite(f, "[7.0, 3.14]");
  $fclose(f);
  concore.simtime = 10;
  concore.readdata(1, "ym", ym_init);
  if (concore.simtime != 10) $fatal(1, "older timestamp: simtime is %f, expected 10", concore.simtime);
  if (concore.data[0] != 3.14) $fatal(1, "older timestamp: data[0] is %f, expected 3.14", concore.data[0]);

  $display("read simtime tests passed");
  $finish;
end
endmodule
