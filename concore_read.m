function [result] = concore_read(port, name, inistr)
     global concore;
     pause(concore.delay);
     try
         input1 = fopen(strcat(concore.inpath,num2str(port),'/',name));
         ins = fscanf(input1,'%c');
         fclose(input1);
     catch exc
         ins = inistr;
     end
     maxretries = 5;
     attempts = 0;
     while length(ins) == 0 && attempts < maxretries
         pause(concore.delay);
         try
             input1 = fopen(strcat(concore.inpath,num2str(port),'/',name));
             ins = fscanf(input1,'%c');
             fclose(input1);
         catch exc
         end
         concore.retrycount = concore.retrycount + 1;
         attempts = attempts + 1;
     end
     if length(ins) == 0
         ins = inistr;
     end
     concore.s = strcat(concore.s, ins);
     % Safe numeric parsing (replaces unsafe eval)
     clean_str = strtrim(ins);
     clean_str = regexprep(clean_str, '[\[\]]', '');
     % Normalize comma delimiters to whitespace so sscanf parses all values
     clean_str = strrep(clean_str, ',', ' ');
     result = sscanf(clean_str, '%f').';
     % Guard against empty parse result to avoid indexing errors
     if isempty(result)
         result = [];
         return;
     end
     concore.simtime = max(concore.simtime, result(1));
     if numel(result) > 1
         result = result(2:end);
     else
         result = [];
     end
end
