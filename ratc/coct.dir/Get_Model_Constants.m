%--------------------------------------------------------------------------
% Set values to model parameters
% 
% Yuyu Yao
% Oct 19, 2020
%--------------------------------------------------------------------------

function [par] = Get_Model_Constants(par)
    % Constant of CVS model
    par.CVS.R1 = 0.01;                  % Systemic resistance
    par.CVS.R2 = 0.0001;                % Mitral Valve Resistance
    par.CVS.R3 = 0.008;                 % Aortic Valve Resistance
    par.CVS.C2 = 20;                    % Veneous compliance
    par.CVS.C3 = 1.8;                   % Systemic compliance
    par.CVS.E_min = 0.02;               % End-diastolic Elastance
    par.CVS.E_max = 1.2;                % End-systolic Elastance
    par.CVS.L = 1e-6;                   % Inertance 
    par.CVS.T0 = 60/450;                % Baseline HR

    % Constant of baroreceptor 
    % Parameters for arterial wall deformation
    par.BR.Am = 15.71;                  % Unstressed aortic cross-sectional area
    par.BR.A0 = 3.14;                   % Maximum aortic cross-sectional area
    par.BR.a = 150;                     % Saturation pressure
    par.BR.k = 5;                       % Steepness constant
    % Parameters for mechanoreceptor model
    par.BR.a1 = 0.4;                    % Nerve ending const
    par.BR.a2 = 0.5;                    
    par.BR.b1 = 0.5;                    % Nerve ending relaxation rate
    par.BR.b2 = 2;
    % Parameters for BR firing model
    par.BR.s1 = 2.947e-10;              % Firing constant
    par.BR.s2 = 3.473e-12;
    par.BR.Cm = 37.5e-11;               % Membrane capacitance 
    par.BR.gl = 5.019e-8;               % Membrane conductance
    par.BR.Vth = 0.00116;               % Voltage threshold
    par.BR.Tr = 0.0062;                 % refractory period

    % Parameters of CNS 
    par.CNS.fes_inf = 3;                % Sympathetic rate with maximum afferent inputs
    par.CNS.fes0 = 16;                  % Sympathetic rate with minimum afferent inputs
    par.CNS.kes = 0.07;                 % Steepness constant for sympathetic pathway
    par.CNS.fev_inf = 6;                % Sympathetic rate with maximum afferent inputs
    par.CNS.fev0 = 3;                   % Sympathetic rate with minimum afferent inputs
    par.CNS.kev = 7;                    % Steepness constant for sympathetic pathway
    par.CNS.fas0 = 30;                  % Central Frequency of Afferent Baroreceptor

    % Parameters of efferent pathways
    par.efrt.tau_E = 8/5;               % Time Constant for Elastance Change
    par.efrt.tau_R = 6/5;               % Time Constant for Systemic Resistance Change
    par.efrt.tau_Ts = 2/5;              % Time Constant for Heart Period Change due to Sympathetic Stimulation
    par.efrt.tau_Tv = 1.5/5;            % Time Constant for Heart Period Change due to Vagal Stimulation
    par.efrt.G_E = 0.3;                 % Gain of Systolic Left Ventricular Elastance Change 
    par.efrt.G_R = 0.06;                % Gain of Systemic Resistance  Change
    par.efrt.G_Ts = -0.01;              % Gain of Heart Period Change by Sympathetic Stimulation
    par.efrt.G_Tv = 0.015;              % Gain of Heart Period Chance by Vagal Stimulation
    par.efrt.fes_min = 3;               % Minimum Sympathetic Frequency
    par.efrt.d_Ts = 0.4;                % Delay in response of cardiac period through sympathetic pathway
    par.efrt.d_Tv = 0.04;               % Delay in response of cardiac period through vagal pathway
    par.efrt.d_E = 0.4;                 % Delay in response of systolic elastance
    par.efrt.d_R = 0.4;                 % Delay in response of systemic resistance
    
    % Constant of Device Model
    par.stm.Gas = 178;                  % Sensitivity of baroreceptive fibers               
    par.stm.Ges = 30;                   % Sensitivity of sympathetic fibers   
    par.stm.Gev = 30;                   % Sensitivity of vagal fibers
    par.stm.kw = 2.5e-4;                % Scaling coefficient of pulse width
    par.stm.kf = 25;                    % Scaling coefficient of pulse frequency
    par.stm.loc = [1  0  0; ...         % Fiber concentration in three stimulation locations
                   0  1  0; ...
                   0  0  1];
end