function concore_default_maxtime(default)
    global concore; 
    try
        maxfile = fopen(strcat(concore.inpath,'1/concore.maxtime'));
        instr = fscanf(maxfile,'%c');
        parsed_val = concore_literal_eval(instr);
        if isnumeric(parsed_val) && numel(parsed_val) == 1
            concore.maxtime = parsed_val;
        else
            concore.maxtime = default;
        end
        fclose(maxfile);
    catch exc 
        concore.maxtime = default;
    end
end
