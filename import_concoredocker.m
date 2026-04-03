function import_concore
    global concore;

    % Docker/Linux environment — no Windows batch file generation
   
  
    iportfile = fopen('concore.iport');
    if iportfile ~= -1
        try
            concore.iports = fscanf(iportfile,'%c');
        catch exc
            concore.iports = '';
        end
        fclose(iportfile);
    else
        concore.iports = '';
    end

    oportfile = fopen('concore.oport');
    if oportfile ~= -1
        try
            concore.oports = fscanf(oportfile,'%c');
        catch exc
            concore.oports = '';
        end
        fclose(oportfile);
    else
        concore.oports = '';
    end

    concore.s = '';
    concore.olds = '';
    concore.delay = 1;
    concore.retrycount = 0;
    if exist('/in1','dir')==7  % 5/20/21  work for docker or local
        concore.inpath = '/in';
        concore.outpath = '/out';
    else
        concore.inpath = 'in';
        concore.outpath = 'out';
    end
    concore.simtime = 0;

    concore_default_maxtime(100);
end
