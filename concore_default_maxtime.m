function concore_default_maxtime(default)
    global concore; 
    try
        maxfile = fopen(strcat(concore.inpath,'1/concore.maxtime'));
        instr = fscanf(maxfile,'%c');
        % Safe numeric parsing (replaces unsafe eval)
        clean_str = strtrim(instr);
        clean_str = regexprep(clean_str, '[\[\]]', '');
        % Normalize commas to whitespace so sscanf can parse all tokens
        clean_str = strrep(clean_str, ',', ' ');
        parsed_values = sscanf(clean_str, '%f');
        if numel(parsed_values) == 1
            concore.maxtime = parsed_values;
        else
            concore.maxtime = default;
        end
        fclose(maxfile);
    catch exc 
        concore.maxtime = default;
    end
end

