function [result] = concore_iport(target)
    global concore;
    s = concore.iports;
    target = strcat('''',target,''':');
    result = 0;
    for i = 1:length(s)-length(target)+1;
        if isequal(s(i:i+length(target)-1),target)
            for j = i+length(target):length(s)
                if isequal(s(j),',')||isequal(s(j),'}')
                   % Safe numeric parsing (replaces unsafe eval)
                   port_str = strtrim(s(i+length(target):j-1));
                   result = sscanf(port_str, '%f');
                   if isempty(result)
                       % Keep the initialized default value (0) if parsing fails
                       result = 0;
                   end
                   return
                end
            end
        end
    end
    display(strcat('no such port:',target));
end 
