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
     while length(ins) == 0
         pause(concore.delay);
         input1 = fopen(strcat(concore.inpath,num2str(port),'/',name));
         ins = fscanf(input1,'%c');
         fclose(input1);
         concore.retrycount = concore.retrycount + 1;
     end
     concore.s = strcat(concore.s, ins);
     result = eval(ins);
     concore.simtime = max(concore.simtime,result(1));
     result = result(2:length(result));
end
