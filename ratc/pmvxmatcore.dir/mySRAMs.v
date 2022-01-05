integer m_index;
reg [15:0] m[511:0]; 
initial
  begin
    for (m_index=0; m_index<=511; m_index = m_index + 1)
       m[m_index] = 16'h4000;
   
m[ 0] = 16'h795c;
m[ 1] = 16'h67e5;
m[ 2] = 16'h68eb;
m[ 3] = 16'h699b;
m[ 4] = 16'h67e5;
m[ 5] = 16'h795f;
m[ 6] = 16'h6bad;
m[ 7] = 16'h6c76;
m[ 8] = 16'h68eb;
m[ 9] = 16'h6bad;
m[10] = 16'h7966;
m[11] = 16'h6e1c;
m[12] = 16'h699b;
m[13] = 16'h6c76;
m[14] = 16'h6e1c;
m[15] = 16'h7971;
m[16] = 16'h4000;
m[17] = 16'h4000;
m[18] = 16'h4000;
m[19] = 16'h4000;
m[20] = 16'hf605;
m[21] = 16'hf918;
m[22] = 16'hfaff;
m[23] = 16'hfc60;
m[24] = 16'h6f72;
m[25] = 16'h7205;
m[26] = 16'h725a;
m[27] = 16'h7518;
m[28] = 16'h7412;
m[29] = 16'h76ff;
m[30] = 16'h753c;
m[31] = 16'h7860;
m[32] = 16'h4000;
m[33] = 16'h4000;
m[34] = 16'h4000;
m[35] = 16'h4000;
m[36] = 16'h4000;
m[37] = 16'h4000;
m[38] = 16'h4000;
m[39] = 16'h4000;
m[40] = 16'h4000;
m[41] = 16'h4000;
m[42] = 16'h0200;
m[43] = 16'h0200;
m[44] = 16'h0200;
m[45] = 16'h0200;
m[46] = 16'h4000;
m[47] = 16'h4000;
  end

always @(sysclk)
  begin
    if (m_en) 
      begin 
        m_do = m[m_addr];
        if (m_we) 
          m[m_addr] = m_di;
      end
    else
      m_do = 16'bzzzzzzzzzzzzzzzz;
  end

/* the Xilinx block ram instantiation
 m_SRAM (
.DO(m_do),
.DOP(m_dop),
.ADDR(m_addr[9:0]),
.CLK(sysclk),
.DI(m_di),
.DIP(2'b0),
.EN(m_en),
.SSR(1'b0),
.WE(m_we)
*/

integer c_index;
reg [15:0] c[511:0]; 

initial
  begin
/*    for (c_index=0; c_index<=511; c_index = c_index + 1)
       c[c_index] = 16'h4000;
    end */
  end

always @(sysclk)
  begin
    if (c_en) 
      begin 
        c_do = c[c_addr];
        if (c_we) 
          c[c_addr] = c_di;
      end
    else
      c_do = 16'bzzzzzzzzzzzzzzzz;
  end

/* the Xilinx block ram instantiation
 c_SRAM (
.DO(c_do),
.DOP(c_dop),
.ADDR(c_addr[9:0]),
.CLK(sysclk),
.DI(c_di),
.DIP(2'b0),
.EN(c_en),
.SSR(1'b0),
.WE(c_we)
*/

