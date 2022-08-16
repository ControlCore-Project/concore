# Rat Cardiac (ratc) models.

This folder consists of ratc studies. Given below is a brief introduction to the files in this folder.

| File 			|		Author	 | Language | Description | Additional Notes |
|---|------|---|---|------|
| c2.m (c2.dir)			|	Yuyu Yao	| Octave |	NMPC (amp) Controller | uses CasADi^* |
| candr.py (candr.dir,Dockerfile.candr)	|	Andrew Branen	| Python	| LSTM (wid) Controller uses Tensorflow |
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
