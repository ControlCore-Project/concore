function [result] = concore_initval(simtime_val)
    global concore;
    % Safe numeric parsing (replaces unsafe eval)
    clean_str = strtrim(simtime_val);
    clean_str = regexprep(clean_str, '[\[\]]', '');
    clean_str = strrep(clean_str, ',', ' ');
    result = sscanf(clean_str, '%f').';
    % Guard against empty or invalid numeric input
    if isempty(result)
        concore.simtime = 0;
        result = [];
        return;
    end
    concore.simtime = result(1);
    if numel(result) >= 2
        result = result(2:end);
    else
        result = [];
    end
end
