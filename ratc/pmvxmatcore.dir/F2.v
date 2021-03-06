`timescale 1ns/100ps

module F2 (zl,f2);
input [4:0] zl;
output [14:0] f2;
reg [14:0] f2;

always @ (zl)
case (zl)
0 : f2 = -2335;
1 : f2 = -2358;
2 : f2 = -2381;
3 : f2 = -2406;
4 : f2 = -2431;
5 : f2 = -2458;
6 : f2 = -2485;
7 : f2 = -2514;
8 : f2 = -2543;
9 : f2 = -2574;
10 : f2 = -2606;
11 : f2 = -2640;
12 : f2 = -2676;
13 : f2 = -2713;
14 : f2 = -2753;
15 : f2 = -2794;
16 : f2 = -2839;
17 : f2 = -2886;
18 : f2 = -2936;
19 : f2 = -2991;
20 : f2 = -3049;
21 : f2 = -3113;
22 : f2 = -3183;
23 : f2 = -3260;
24 : f2 = -3347;
25 : f2 = -3445;
26 : f2 = -3558;
27 : f2 = -3692;
28 : f2 = -3857;
29 : f2 = -4069;
30 : f2 = -4368;
31 : f2 = -4879;
default : f2 = 0;
endcase

endmodule