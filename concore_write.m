function concore_write(port, name, val, delta)
     global concore;
     try
         out_dir = cat(2, concore.outpath, num2str(port), '/');
         output1 = fopen(cat(2, out_dir, name), "w");
         st_val = concore.simtime + delta;
         st_str = sprintf('%.17g', st_val);

         if isempty(val)
             outstr = ['[', st_str, ']'];
         elseif iscell(val)
             items = cell(1, numel(val) + 1);
             items{1} = st_str;
             for k = 1:numel(val)
                 items{k+1} = concore_literal_serialize(val{k});
             end
             outstr = ['[', strjoin(items, ', '), ']'];
         elseif ischar(val)
             outstr = ['[', st_str, ', ', concore_literal_serialize(val), ']'];
         elseif isstring(val) && numel(val) == 1
             outstr = ['[', st_str, ', ', concore_literal_serialize(char(val)), ']'];
         elseif islogical(val)
             if numel(val) == 1
                 outstr = ['[', st_str, ', ', concore_literal_serialize(val), ']'];
             else
                 items = cell(1, numel(val) + 1);
                 items{1} = st_str;
                 for k = 1:numel(val)
                     items{k+1} = concore_literal_serialize(val(k));
                 end
                 outstr = ['[', strjoin(items, ', '), ']'];
             end
         elseif isnumeric(val)
             if numel(val) == 1
                 outstr = ['[', st_str, ', ', sprintf('%.17g', val), ']'];
             else
                 sz = size(val);
                 if sz(1) == 1 || sz(2) == 1
                     items = cell(1, numel(val) + 1);
                     items{1} = st_str;
                     for k = 1:numel(val)
                         items{k+1} = sprintf('%.17g', val(k));
                     end
                     outstr = ['[', strjoin(items, ', '), ']'];
                 else
                     outstr = ['[', st_str, ', ', concore_literal_serialize(val), ']'];
                 end
             end
         else
             outstr = ['[', st_str, ', ', concore_literal_serialize(val), ']'];
         end

         fprintf(output1, '%s', outstr);
         fclose(output1);
         % simtime must not be mutated here (issue #385).
     catch exc
         disp(['skipping ' concore.outpath num2str(port) '/' name]);
     end
end
