`define PROCESSOR_DELAY 800

`define LNS_MAX_VAL 4294967296.0
`define INT_ZERO  16'h4000 /*internal rep of 0.0*/
`define INT_ONE   16'h0000 /*internal rep of 1.0*/

`define NORM_STATUS      16'b0000_0000_0000_0000
`define BUSY_MASK_STATUS 16'b1000_0000_0000_0000
`define BUSY_CI_STATUS   16'b1100_0000_0000_0000
`define BUSY_DCD_STATUS  16'b1010_0000_0000_0000
`define BUSY_DI_STATUS   16'b1001_0000_0000_0000
`define BUSY_DO_STATUS   16'b1000_1000_0000_0000
`define BUSY_PROC_STATUS 16'b1000_0100_0000_0000

`define COMMAND_RESET            0
`define COMMAND_SET_N            1
`define COMMAND_GET_A            14
`define COMMAND_GET_C            15
`define COMMAND_PUT_A            16
`define COMMAND_PUT_C            17
`define COMMAND_GET_PIVOT        27
`define COMMAND_PUT_PIVOT        28
`define COMMAND_GET_X            29
`define COMMAND_PUT_X            30

`define COMMAND_SET_RC           31

`define COMMAND_INPUT_C          2
`define COMMAND_OUTPUT_C         3
`define COMMAND_OUTPUT_A         9
`define COMMAND_OUTPUT_M         39

`define COMMAND_STORE_C          4
`define COMMAND_LOAD_C           5
`define COMMAND_LOAD_TRANSPOSE_C 18
`define COMMAND_LOAD_A           20
`define COMMAND_STORE_CLEAR_A    6
`define COMMAND_STORE_IDENT_A    13
`define COMMAND_ADD_A            7
`define COMMAND_ADD_SCALAR_A     40
`define COMMAND_MUL_C            8  //multiply C with a vector in memory on the left (BC)
`define COMMAND_MUL_CR           32 //multiply C with a vector in memory on the right (CB)
`define COMMAND_MUL_SCALAR_A     35 //multiply C with a sclar and store in a

`define COMMAND_MULVEC_C         10 //multiply C with a vector in memory on the left (bC)
`define COMMAND_MULVEC_CR_RECT   33 //multiply C with a vector in memory on the right (Cb) and using n and n_row as dimensionts
`define COMMAND_MULVEC_C_RECT    34 //multiply C with a vector in memory on the left (bC) and using n and n_row as dimensionts
`define COMMAND_MUL2_COMP        36
`define COMMAND_MUL3_COMP        37
`define COMMAND_SUM_A            38

`define COMMAND_STORE_CLEAR_VECA 11
`define COMMAND_ADDVEC_A         12
`define COMMAND_STORE_ROWA       19
`define COMMAND_STORE_ROWC       21
`define COMMAND_ADDSCALVEC_A     22
`define COMMAND_ADDSCALVEC_C     23
`define COMMAND_LOAD_ROWA        24
`define COMMAND_LOAD_ROWC        25
`define COMMAND_FIND_PIVOT       26