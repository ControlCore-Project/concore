function import_concore
    global concore;

    if ispc
        try
          pid = getpid();
        catch exc
          pid = feature('getpid');
        end
        outputpid = fopen('concorekill.bat','w');
        if outputpid ~= -1
            fprintf(outputpid,'%s',['taskkill /F /PID ',num2str(pid)]);
            fclose(outputpid);
        else
            warning('import_concore:ConcoreKillFileOpenFailed', ...
                'Could not create concorekill.bat. Continuing without kill script.');
        end
    end
   
  
    try
      iportfile = fopen('concore.iport');
      concore.iports = fscanf(iportfile,'%c');
      if isnumeric(iportfile) && iportfile ~= -1
          fclose(iportfile);
      end
      iportfile = -1;
    catch exc
      if exist('iportfile', 'var') && isnumeric(iportfile) && iportfile ~= -1
          fclose(iportfile);
      end
      iportfile = -1;
    end

    try
      oportfile = fopen('concore.oport');
      concore.oports = fscanf(oportfile,'%c');
      if isnumeric(oportfile) && oportfile ~= -1
          fclose(oportfile);
      end
      oportfile = -1;
    catch exc
      if exist('oportfile', 'var') && isnumeric(oportfile) && oportfile ~= -1
          fclose(oportfile);
      end
      oportfile = -1;
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
