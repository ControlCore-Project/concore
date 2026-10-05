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

     % Python-literal-compatible parsing
     try
         parsed = concore_literal_eval(ins);
     catch exc
         try
             parsed = concore_literal_eval(inistr);
         catch exc2
             parsed = [];
         end
     end

     if isempty(parsed)
         result = [];
         return;
     end

     if iscell(parsed)
         if isempty(parsed)
             result = [];
             return;
         end
         first_elem = parsed{1};
         if isnumeric(first_elem) || islogical(first_elem)
             concore.simtime = max(concore.simtime, double(first_elem));
         end
         if numel(parsed) > 1
             % If all remaining elements are numeric scalars, return numeric row vector
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
         concore.simtime = max(concore.simtime, parsed(1));
         if numel(parsed) > 1
             result = parsed(2:end);
         else
             result = [];
         end
     else
         result = parsed;
     end
end
