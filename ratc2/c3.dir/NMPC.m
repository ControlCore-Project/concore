function [usim, psim, status, xsp, usp, xprior, dprior] = NMPC(t, ym, usim, psim, ysp, status, xsp, usp, xprior, dprior, regulator, sstarg, estmtr, disturbancemodel)
% inputs: t ~ cardiac cycle
%         ym ~ measurement (mean AP, heart period)
%         usim ~ past continuous input (I, freq for 3 locations)
%         psim ~ past active locations
%         ysp ~ setpoint for outputs
%         xsp ~ setpoint for states(constant if ysp does'n change)
%         usp ~ setpoint for inputs
%         xprior ~ previous estimated states
%         dprior ~ previous estimated disturbance
%         regulator, sstarg, estimate ~ solver for regulator, steady-state
%         calculator, and estimator
% outputs: current calculated


% Set horizon.
Ne = 10;
estmtr.truncatehorizon(min(t - 1, Ne))
% Get new measurement.
if t > 1
    estmtr.newmeasurement(ym, [psim; usim]);
end
estmtr.par.x0bar = xprior(:, 1);
estmtr.par.d0bar = dprior(:, 1);

% Solve MHE problem and save state estimate.
estmtr.solve();
% Used for warm start at next timestep.
estmtr.saveguess();  
fprintf('Step %d: %s\n', t, estmtr.status);
if ~isequal(estmtr.status, 'Solve_Succeeded')
    warning('Solver failure at time %d!', t);
end

if t <= Ne
    xhat = estmtr.var.x(:, t);
    dhat = estmtr.var.d(:, t);
else
    xhat = estmtr.var.x(:, end);
    dhat = estmtr.var.d(:, end);
end 
xprior = [xprior(:,2:end), xhat];
dprior = [dprior(:,2:end), dhat];
 
if t > Ne
    regulator_prev = 1e6;
    i = 0;
    for loc1 = 0:1
        for loc2 = 0:1
            for loc3 = 0:1
                i = i + 1;
                switch disturbancemodel
                    case 'Good'
                        % Use steady-state target finder.
                        sstarg.fixvar('y', 1, ysp(:, t));
                        sstarg.par.p = [loc1; loc2; loc3];
                        sstarg.par.d = dhat;
                        sstarg.solve();
                        sstarg.saveguess();
                        fprintf('%1s %2d %2d %2d %10s %3d: %s\n', 'Combination', loc1, loc2, loc3, 'sstarg', t, sstarg.status);
                            % Set steady state values to x and u. 
                            if isequal(sstarg.status, 'Solve_Succeeded')
                                xsp(:, i) = sstarg.var.x;
                                usp(:, i) = sstarg.var.u;
                                status(i) = 1;
                            else
                                status(i) = 0;
                            end

                    case 'No'
                        if t == Ne + 1 || ~isequal(ysp(:, t), ysp(:, t-1))
                        % Use steady-state target finder.
                        sstarg.fixvar('y', 1, ysp(:, t));
                        sstarg.par.p = [loc1; loc2; loc3];
                        sstarg.solve();
                        sstarg.saveguess();
                        fprintf('%1s %2d %2d %2d %10s %3d: %s\n', 'Combination', loc1, loc2, loc3, 'sstarg', t, sstarg.status);
                            % Set steady state values to x and u. 
                            if isequal(sstarg.status, 'Solve_Succeeded')
                                xsp(:, i) = sstarg.var.x;
                                usp(:, i) = sstarg.var.u;
                                status(i) = 1;
                            else
                                status(i) = 0;
                            end
                        end
                end
                
                if status(i) == 1
                    regulator.par.xsp = xsp(:, i);
                    regulator.par.usp = usp(:, i);
                    regulator.par.d = dhat;
                    regulator.par.p = [loc1; loc2; loc3];
                    regulator.fixvar('x', 1, xhat);
                    regulator.solve();
                    regulator.saveguess();
                    if isequal(regulator.status, 'Solve_Succeeded')&& regulator.obj < regulator_prev
                         psim = [loc1; loc2; loc3];
                         usim = regulator.var.u(:,1);
                         if loc1 == 0
                             usim(1) = 0;
                             usim(2) = 0;                     
                         end
                         if loc2 == 0
                             usim(3) = 0;
                             usim(4) = 0;                     
                         end
                         if loc3 == 0
                             usim(5) = 0;
                             usim(6) = 0;                     
                         end     
                         regulator_prev = regulator.obj;
                    end       
                end
            end
        end
    end
end
end