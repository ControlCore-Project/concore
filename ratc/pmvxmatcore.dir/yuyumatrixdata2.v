initial 
begin
/*array([[ 0.88450827,  0.09479982, -0.01563224,  0.02843792, -0.02381475,
         0.00394992],
       [ 0.01441458,  0.62814172,  0.01493515,  0.00170917,  0.08300119,
        -0.0128421 ],
       [-0.00999643, -0.09339063,  0.99739109, -0.03657221,  0.02649131,
         0.03018569],
       [-0.05335715, -0.05218417,  0.03451499,  0.81103519, -0.47459787,
         0.71316841],
       [ 0.0154948 , -0.05402746,  0.01212646,  0.49077367, -0.0045279 ,
        -0.02164305],
       [ 0.03187534, -0.03837947, -0.0301056 ,  0.00149132, -0.22608616,
         0.93440215]])
*/
matrixLNSproc_inst.matrixproc_inst.m[ 0]=testMPC.realtolns(0.88450827);  
matrixLNSproc_inst.matrixproc_inst.m[ 1]=testMPC.realtolns(0.09479982); 
matrixLNSproc_inst.matrixproc_inst.m[ 2]=testMPC.realtolns(-0.01563224);  
matrixLNSproc_inst.matrixproc_inst.m[ 3]=testMPC.realtolns(0.02843792); 
matrixLNSproc_inst.matrixproc_inst.m[ 4]=testMPC.realtolns(-0.02381475);         
matrixLNSproc_inst.matrixproc_inst.m[ 5]=testMPC.realtolns(0.00394992);
matrixLNSproc_inst.matrixproc_inst.m[ 6]=testMPC.realtolns(0.01441458);  
matrixLNSproc_inst.matrixproc_inst.m[ 7]=testMPC.realtolns(0.62814172);  
matrixLNSproc_inst.matrixproc_inst.m[ 8]=testMPC.realtolns(0.01493515);  
matrixLNSproc_inst.matrixproc_inst.m[ 9]=testMPC.realtolns(0.00170917);  
matrixLNSproc_inst.matrixproc_inst.m[10]=testMPC.realtolns(0.08300119);        
matrixLNSproc_inst.matrixproc_inst.m[11]=testMPC.realtolns(-0.0128421);
matrixLNSproc_inst.matrixproc_inst.m[12]=testMPC.realtolns(-0.00999643); 
matrixLNSproc_inst.matrixproc_inst.m[13]=testMPC.realtolns(-0.09339063);  
matrixLNSproc_inst.matrixproc_inst.m[14]=testMPC.realtolns(0.99739109); 
matrixLNSproc_inst.matrixproc_inst.m[15]=testMPC.realtolns(-0.03657221);  
matrixLNSproc_inst.matrixproc_inst.m[16]=testMPC.realtolns(0.02649131);
matrixLNSproc_inst.matrixproc_inst.m[17]=testMPC.realtolns(0.03018569);
matrixLNSproc_inst.matrixproc_inst.m[18]=testMPC.realtolns(-0.05335715); 
matrixLNSproc_inst.matrixproc_inst.m[19]=testMPC.realtolns(-0.05218417);  
matrixLNSproc_inst.matrixproc_inst.m[20]=testMPC.realtolns(0.03451499);  
matrixLNSproc_inst.matrixproc_inst.m[21]=testMPC.realtolns(0.81103519); 
matrixLNSproc_inst.matrixproc_inst.m[22]=testMPC.realtolns(-0.47459787);
matrixLNSproc_inst.matrixproc_inst.m[23]=testMPC.realtolns(0.71316841);
matrixLNSproc_inst.matrixproc_inst.m[24]=testMPC.realtolns(0.0154948); 
matrixLNSproc_inst.matrixproc_inst.m[25]=testMPC.realtolns(-0.05402746);  
matrixLNSproc_inst.matrixproc_inst.m[26]=testMPC.realtolns(0.01212646);  
matrixLNSproc_inst.matrixproc_inst.m[27]=testMPC.realtolns(0.49077367); 
matrixLNSproc_inst.matrixproc_inst.m[28]=testMPC.realtolns(-0.0045279);
matrixLNSproc_inst.matrixproc_inst.m[29]=testMPC.realtolns(-0.02164305);
matrixLNSproc_inst.matrixproc_inst.m[30]=testMPC.realtolns(0.03187534); 
matrixLNSproc_inst.matrixproc_inst.m[31]=testMPC.realtolns(-0.03837947); 
matrixLNSproc_inst.matrixproc_inst.m[32]=testMPC.realtolns(-0.0301056);
matrixLNSproc_inst.matrixproc_inst.m[33]=testMPC.realtolns(0.00149132); 
matrixLNSproc_inst.matrixproc_inst.m[34]=testMPC.realtolns(-0.22608616);
matrixLNSproc_inst.matrixproc_inst.m[35]=testMPC.realtolns(0.93440215);

/*>>> xm
array([[-0.02681762],
       [ 0.1406961 ],
       [-0.93224027],
       [ 0.45825474],
       [ 1.41566324],
       [ 0.62171553]])
*/
`define ADDRXM 36
matrixLNSproc_inst.matrixproc_inst.m[36]=testMPC.realtolns(-0.02681762);
matrixLNSproc_inst.matrixproc_inst.m[37]=testMPC.realtolns(0.1406961 );
matrixLNSproc_inst.matrixproc_inst.m[38]=testMPC.realtolns(-0.93224027);
matrixLNSproc_inst.matrixproc_inst.m[39]=testMPC.realtolns(0.45825474);
matrixLNSproc_inst.matrixproc_inst.m[40]=testMPC.realtolns(1.41566324);
matrixLNSproc_inst.matrixproc_inst.m[41]=testMPC.realtolns(0.62171553);

/*>>> u
array([[3.93851985e-04],
       [4.00000029e+01],
       [7.18728120e-05],
       [7.00000645e+00],
       [9.66836416e-05],
       [1.00000106e+01]])
*/
matrixLNSproc_inst.matrixproc_inst.m[42]=testMPC.realtolns(3.93851985e-4);
matrixLNSproc_inst.matrixproc_inst.m[43]=testMPC.realtolns(40.0);
matrixLNSproc_inst.matrixproc_inst.m[44]=testMPC.realtolns(7.18728120e-5);
matrixLNSproc_inst.matrixproc_inst.m[45]=testMPC.realtolns(7.0);
matrixLNSproc_inst.matrixproc_inst.m[46]=testMPC.realtolns(9.66836416e-5);
matrixLNSproc_inst.matrixproc_inst.m[47]=testMPC.realtolns(10.0);
/*
>>> X['B']
array[[-1.42333064e+01  1.50096116e-03, -2.91069379e+02,
        -1.42940498e-03, -3.40903515e+02, -3.34554587e-04],
       [ 1.74021612e+02, -4.91152132e-03, -1.76862951e+01,
        -6.97658383e-03,  1.32167370e+03,  6.57329262e-04],
       [ 5.40534656e+01, -1.56834706e-03, -6.05935552e+01,
        -3.12506847e-03,  4.05846119e+02, -6.31985027e-05],
       [-3.37517726e+02,  1.53032887e-02, -6.80657025e+02,
         1.37825197e-02, -2.54343610e+03,  7.22846364e-03],
       [-8.79452588e+02,  4.53586896e-02, -1.03531406e+03,
         5.82589703e-02, -8.17571161e+03,  2.18993594e-02],
       [-1.69863442e+02,  1.19898767e-02, -2.77474759e+02,
         1.42324103e-02, -2.19801371e+03,  5.85070945e-03]])
*/
matrixLNSproc_inst.matrixproc_inst.m[48]=testMPC.realtolns(-14.2333064);
//$display("%h",matrixLNSproc_inst.matrixproc_inst.m[48]);
//$display(1.50096116e-3);
matrixLNSproc_inst.matrixproc_inst.m[49]=testMPC.realtolns(1.50096116e-3);
//$display("%h",matrixLNSproc_inst.matrixproc_inst.m[49]);
matrixLNSproc_inst.matrixproc_inst.m[50]=testMPC.realtolns(-2.91069379e2);
matrixLNSproc_inst.matrixproc_inst.m[51]=testMPC.realtolns(-1.42940498e-3); 
matrixLNSproc_inst.matrixproc_inst.m[52]=testMPC.realtolns(-3.40903515e2); 
matrixLNSproc_inst.matrixproc_inst.m[53]=testMPC.realtolns(-3.34554587e-4);
matrixLNSproc_inst.matrixproc_inst.m[54]=testMPC.realtolns( 1.74021612e2); 
matrixLNSproc_inst.matrixproc_inst.m[55]=testMPC.realtolns(-4.91152132e-3); 
matrixLNSproc_inst.matrixproc_inst.m[56]=testMPC.realtolns(-1.76862951e1);
matrixLNSproc_inst.matrixproc_inst.m[57]=testMPC.realtolns(-6.97658383e-3);  
matrixLNSproc_inst.matrixproc_inst.m[58]=testMPC.realtolns(1.32167370e3);  
matrixLNSproc_inst.matrixproc_inst.m[59]=testMPC.realtolns(6.57329262e-4);
matrixLNSproc_inst.matrixproc_inst.m[60]=testMPC.realtolns(5.40534656e1); 
matrixLNSproc_inst.matrixproc_inst.m[61]=testMPC.realtolns(-1.56834706e-3); 
matrixLNSproc_inst.matrixproc_inst.m[62]=testMPC.realtolns(-6.05935552e1);
matrixLNSproc_inst.matrixproc_inst.m[63]=testMPC.realtolns(-3.12506847e-3);  
matrixLNSproc_inst.matrixproc_inst.m[64]=testMPC.realtolns(4.05846119e2); 
matrixLNSproc_inst.matrixproc_inst.m[65]=testMPC.realtolns(-6.31985027e-5);
matrixLNSproc_inst.matrixproc_inst.m[66]=testMPC.realtolns(-3.37517726e2);  
matrixLNSproc_inst.matrixproc_inst.m[67]=testMPC.realtolns(1.53032887e-2); 
matrixLNSproc_inst.matrixproc_inst.m[68]=testMPC.realtolns(-6.80657025e2);
matrixLNSproc_inst.matrixproc_inst.m[69]=testMPC.realtolns(1.37825197e-2); 
matrixLNSproc_inst.matrixproc_inst.m[70]=testMPC.realtolns(-2.54343610e3);  
matrixLNSproc_inst.matrixproc_inst.m[71]=testMPC.realtolns(7.22846364e-3);
matrixLNSproc_inst.matrixproc_inst.m[72]=testMPC.realtolns(-8.79452588e2);  
matrixLNSproc_inst.matrixproc_inst.m[73]=testMPC.realtolns(4.53586896e-2); 
matrixLNSproc_inst.matrixproc_inst.m[74]=testMPC.realtolns(-1.03531406e3);
matrixLNSproc_inst.matrixproc_inst.m[75]=testMPC.realtolns(5.82589703e-2); 
matrixLNSproc_inst.matrixproc_inst.m[76]=testMPC.realtolns(-8.17571161e3);  
matrixLNSproc_inst.matrixproc_inst.m[77]=testMPC.realtolns(2.18993594e-2);
matrixLNSproc_inst.matrixproc_inst.m[78]=testMPC.realtolns(-1.69863442e2);  
matrixLNSproc_inst.matrixproc_inst.m[79]=testMPC.realtolns(1.19898767e-2); 
matrixLNSproc_inst.matrixproc_inst.m[80]=testMPC.realtolns(-2.77474759e2);
matrixLNSproc_inst.matrixproc_inst.m[81]=testMPC.realtolns( 1.42324103e-2); 
matrixLNSproc_inst.matrixproc_inst.m[82]=testMPC.realtolns(-2.19801371e3);  
matrixLNSproc_inst.matrixproc_inst.m[83]=testMPC.realtolns(5.85070945e-3);

/*>>> X['C']
array([[ -49.69744579,    8.18052968, -117.98819451,    5.22199923,
          -4.93643782,    3.80349469],
       [  62.16660134,    6.17460377, -420.20259273,    9.98898037,
         -28.90380971,   32.06640881]])

*/
matrixLNSproc_inst.matrixproc_inst.m[84]=testMPC.realtolns(-49.69744579);    
matrixLNSproc_inst.matrixproc_inst.m[85]=testMPC.realtolns(8.18052968); 
matrixLNSproc_inst.matrixproc_inst.m[86]=testMPC.realtolns(-117.98819451);    
matrixLNSproc_inst.matrixproc_inst.m[87]=testMPC.realtolns(5.22199923);          
matrixLNSproc_inst.matrixproc_inst.m[88]=testMPC.realtolns(-4.93643782);    
matrixLNSproc_inst.matrixproc_inst.m[89]=testMPC.realtolns(3.80349469);
matrixLNSproc_inst.matrixproc_inst.m[90]=testMPC.realtolns(62.16660134);    
matrixLNSproc_inst.matrixproc_inst.m[91]=testMPC.realtolns(6.17460377); 
matrixLNSproc_inst.matrixproc_inst.m[92]=testMPC.realtolns(-420.202592);    
matrixLNSproc_inst.matrixproc_inst.m[93]=testMPC.realtolns(9.98898037);
matrixLNSproc_inst.matrixproc_inst.m[94]=testMPC.realtolns(-28.90380971);   
matrixLNSproc_inst.matrixproc_inst.m[95]=testMPC.realtolns(32.06640881);
/*
matrixLNSproc_inst.matrixproc_inst.m[84]=testMPC.realtolns(0.0);    
matrixLNSproc_inst.matrixproc_inst.m[85]=testMPC.realtolns(0.0); 
matrixLNSproc_inst.matrixproc_inst.m[86]=testMPC.realtolns(0.0);    
matrixLNSproc_inst.matrixproc_inst.m[87]=testMPC.realtolns(1.0);          
matrixLNSproc_inst.matrixproc_inst.m[88]=testMPC.realtolns(0.0);    
matrixLNSproc_inst.matrixproc_inst.m[89]=testMPC.realtolns(0.0);
matrixLNSproc_inst.matrixproc_inst.m[90]=testMPC.realtolns(0.0);    
matrixLNSproc_inst.matrixproc_inst.m[91]=testMPC.realtolns(0.0); 
matrixLNSproc_inst.matrixproc_inst.m[92]=testMPC.realtolns(0.0);    
matrixLNSproc_inst.matrixproc_inst.m[93]=testMPC.realtolns(0.0);
matrixLNSproc_inst.matrixproc_inst.m[94]=testMPC.realtolns(1.0);   
matrixLNSproc_inst.matrixproc_inst.m[95]=testMPC.realtolns(0.0);

*/


/*
>>> X['D']
array([[ 6.36726646e+02,  1.00439100e-02,  5.92512143e+02,
        -1.76384821e-02, -1.02459421e+03, -2.99509106e-03],
       [ 4.54515165e+03, -2.88884321e-02,  1.85862174e+04,
         1.20000520e-01, -1.43991627e+04, -1.87894452e-01]])
*/
matrixLNSproc_inst.matrixproc_inst.m[96]=testMPC.realtolns(6.36726646e2);  
matrixLNSproc_inst.matrixproc_inst.m[97]=testMPC.realtolns(1.00439100e-2);  
matrixLNSproc_inst.matrixproc_inst.m[98]=testMPC.realtolns(5.92512143e2);
matrixLNSproc_inst.matrixproc_inst.m[99]=testMPC.realtolns(-1.76384821e-2); 
matrixLNSproc_inst.matrixproc_inst.m[100]=testMPC.realtolns(-1.02459421e3); 
matrixLNSproc_inst.matrixproc_inst.m[101]=testMPC.realtolns(-2.99509106e-3);
matrixLNSproc_inst.matrixproc_inst.m[102]=testMPC.realtolns(4.54515165e3); 
matrixLNSproc_inst.matrixproc_inst.m[103]=testMPC.realtolns(-2.88884321e-2);  
matrixLNSproc_inst.matrixproc_inst.m[104]=testMPC.realtolns(1.85862174e4);         
matrixLNSproc_inst.matrixproc_inst.m[105]=testMPC.realtolns(1.20000520e-1); 
matrixLNSproc_inst.matrixproc_inst.m[106]=testMPC.realtolns(-1.43991627e4); 
matrixLNSproc_inst.matrixproc_inst.m[107]=testMPC.realtolns(-1.87894452e-1);

/*>>> Plant(u,xm,X)[0]
array([[-0.02683409],
       [ 0.14069634],
       [-0.93223812],
       [ 0.45822299],
       [ 1.41562386],
       [ 0.62173817]])
>>> Plant(u,xm,X)[1]
array([[110.6890829 ],
       [374.06630104]])
*/
end
