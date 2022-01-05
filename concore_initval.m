function [result] = concore_initval(simtime_val)
    global concore;
    result = eval(simtime_val);
    concore.simtime = result(1);
    result = result(2:length(result));
end
