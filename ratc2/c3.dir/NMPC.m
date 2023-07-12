function [usim, psim, status, xsp, usp] = NMPC(t, ym, usim, psim, ysp, status, xsp, usp, regulator, sstarg, estmtr)
Ne = 10;
% Set horizon.
estmtr.truncatehorizon(min(t - 1, Ne))
% Get new measurement.
if t > 1
    estmtr.newmeasurement(ym, [psim; usim]);
end
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
else
    xhat = estmtr.var.x(:, end);
end 
if t > Ne
    regulator_prev = 1e6;
    i = 0;  
    for loc1 = 0:1
        for loc2 = 0:1
            for loc3 = 0:1
                i = i + 1;
                if t == Ne + 1 || ~isequal(ysp(:, t), ysp(:, t-1))
                    % Use steady-state target finder.
                    sstarg.fixvar('y', 1, ysp(:, t));
                    sstarg.par.p = [loc1; loc2; loc3];
                    sstarg.solve();
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

                if status(i) == 1
                    regulator.par.xsp = repmat(xsp(:, i), 1, regulator.horizon + 1);
                    regulator.par.usp = repmat(usp(:, i), 1, regulator.horizon);
                    regulator.par.p = repmat([loc1; loc2; loc3], 1, regulator.horizon+1);
                    regulator.fixvar('x', 1, xhat);
                    regulator.solve();
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