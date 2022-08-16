# Rat Cardiac (ratc) models.

This folder consists of ratc studies. Given below is a brief introduction to the files in this folder.

| File 			|		Author	 | Language | Description | Additional Notes |
|---|------|---|---|------|
| c2.m (c2.dir)			|	Yuyu Yao	| Octave |	NMPC (amp) Controller | uses CasADi^* |
| candr.py (candr.dir,Dockerfile.candr)	|	Andrew Branen	| Python	| LSTM (wid) Controller | uses Tensorflow |
| coct.m (coct.dir)		|		Yuyu Yao	| Matlab |	MMPC (wid) Controller^ |
| cvxpymatcore.py (cvxpymatcore.dir) |		Yuyu Yao |	Python	| MPC (wid) Controller | uses cvxopt^ |
| cwrap.py (cwrap.dir)		|	Mark Arnold	| Python |	Controller wrapper (wid/amp) | 
| plotu.py |					Mark Arnold	| Python	| Plot u (6 values, wid/amp) |
| plotym.py		|		Mark Arnold	| Python	| Plot ym (2 values, HR/MAP) |
| pm2.m (pm2.dir)	|			Yuyu Yao	| Matlab |	Diseased Pulsatile PM* (amp) |
| pmcvxpymatcore.py (pmcvxpymatcore.dir) |	Mark Arnold |	Python |	Linear Nonpulsatile PM (wid) |
| pmoct.m (pmoct.dir)		|	Yuyu Yao	| Matlab	| Healthy Pulsatile PM (wid) |
| pmsid.py			|		Siddharth Prabhu |	Python	| Healthy Pulsatile PM (wid) |
| pmvxmatcore.v (pmvxmatcore.dir)	|	Mark Arnold	| Verilog	| 16-bit Linear Nonpulsatile PM (wid) |
| pwrap.py (pwrap.dir)		|	Mark Arnold	| Python |	PM wrapper (wid/amp) |
| run_pm2.sh  (run_pm2.dir)		|	Mark Arnold	| Shell	| MCR Compiled version of pm2 |
| run_pmoct.sh (run_pmoct.dir) |		Mark Arnold	| Shell	| MCR Compiled version of pmoct |

^Mark removed plotting from controller

*Mark converted to HR for compatibility with plotym.py

The studies and the respective programs are given below.


| Study 			|		Program |
|---------|------------|
|andrC.graphml		| candr.py cwrap.py|
|andrM.graphml		| candr.py pmoct.m|
|andrshM.graphml	|	candr.py run_pmoct.sh|
|sidZ.graphml	|	cvxpymatcore.py pmsid.py|
|sidZPlt2.graphml |		cvxpymatcore.py pmsid.py plotu.py plotym.py|
|yu2MM.graphml	|	c2.m pm2.m |
|yu2MMPlt2.graphml |	c2.m pm2.m plotu.py plotym.py 	|
|yu2MshM.graphml	|	c2.m run_pm2.sh|
|yu2MshMPlt2.graphml |	c2.m run_pm2.sh plotu.py plotym.py|
|yuoctM.graphml		| cvxpymatcore.py pmoct.m |
|yuoctMM.graphml	|	coct.m pmoct.m |
|yuoctMMPlt2.graphml |	coct.m pmoct.m plotu.py plotym.py 	|
|yuoctshM.graphml		| coct.m run_pmoct.sh |
|yuoctshMPull.graphml |	coct.m run_pmoct (pulls from markgarnold Docker repository) 	|
|yuyuC.graphml		| cvxpymatcore.py cwrap.py |
|yuyu.graphml		| cvxpymatcore.py pmcvxpymatcore.py| 
|yuyuP.graphml	|	pwrap.py pmcvxpymatcore.py |
|yuyuPlt2.graphml	|	cvxpymatcore.py pmcvxpymatcore.py plotu.py plotym.py |
|yuyuV.graphml		| cvxpymatcore.py pmvxmatcore.v|
