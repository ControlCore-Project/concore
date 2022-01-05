function concore_default_maxtime(default)
    global concore; 
    try
        maxfile = fopen(strcat(concore.inpath,'1/concore.maxtime'));
        instr = fscanf(maxfile,'%c');
        concore.maxtime = eval(instr);
        fclose(maxfile);
    catch exc 
        concore.maxtime = default;
    end
end

