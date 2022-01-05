function concore_write(port, name, val, delta)
     global concore;
     try
         output1 = fopen(cat(2,concore.outpath, num2str(port), '/', name),"w");
         outstr = cat(2,"[",num2str(concore.simtime+delta),num2str(val,",%e"),"]");
         fprintf(output1,'%s',outstr);
         fclose(output1);
     catch exc
         disp(['skipping ' concore.outpath num2str(port) '/' name]);
     end
end
