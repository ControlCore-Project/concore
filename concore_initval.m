function [result] = concore_initval(simtime_val)
    global concore;
    try
        parsed = concore_literal_eval(simtime_val);
    catch exc
        concore.simtime = 0;
        result = [];
        return;
    end

    if isempty(parsed)
        concore.simtime = 0;
        result = [];
        return;
    end

    if iscell(parsed)
        if isempty(parsed)
            concore.simtime = 0;
            result = [];
            return;
        end
        first_elem = parsed{1};
        if isnumeric(first_elem) || islogical(first_elem)
            concore.simtime = double(first_elem);
        else
            concore.simtime = 0;
        end
        if numel(parsed) >= 2
            all_num_scalar = true;
            for k = 2:numel(parsed)
                if ~isnumeric(parsed{k}) || numel(parsed{k}) ~= 1
                    all_num_scalar = false;
                    break;
                end
            end
            if all_num_scalar
                result = cell2mat(parsed(2:end));
            else
                result = parsed(2:end);
            end
        else
            result = [];
        end
    elseif isnumeric(parsed)
        concore.simtime = parsed(1);
        if numel(parsed) >= 2
            result = parsed(2:end);
        else
            result = [];
        end
    else
        concore.simtime = 0;
        result = parsed;
    end
end
