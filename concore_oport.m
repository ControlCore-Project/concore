function [result] = concore_oport(target)
    global concore;
    s = concore.oports;
    target = strcat('''',target,''':');
    result = 0;
    for i = 1:length(s)-length(target)+1;
        if isequal(s(i:i+length(target)-1),target)
            for j = i+length(target):length(s)
                if isequal(s(j),',')||isequal(s(j),'}')
                   % Safe numeric parsing (replaces unsafe eval)
                   port_str = strtrim(s(i+length(target):j-1));
                   result = sscanf(port_str, '%f');
                   return
                end
            end
        end
    end
    display(strcat('no such port:',target));
end 
