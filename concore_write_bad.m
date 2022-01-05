function concore_write(port, name, val, delta)
     global concore;
     if isstring(val)
         pause(2.*concore.delay);
     elseif ischar(val)
         pause(2.*concore.delay);
     elseif isrow(val) == 0
         disp('val for write must have list or string');
         quit();
     endif
     try
         output1 = fopen(cat(2,concore.outpath, num2str(port), '/', name),"w");
         if nargin == 3 
            outstr = cat(2,"[",num2str(concore.simtime),num2str(val,",%e"),"]");
         else
            outstr = cat(2,"[",num2str(concore.simtime+delta),num2str(val,",%e"),"]");
         endif
         if ischar(val) || isstring(val)
             fprintf(output1,'%s',val);
         else
             fprintf(output1,'%s',outstr);
         endif
         fclose(output1);
     catch exc
         disp(['skipping ' concore.outpath num2str(port) '/' name]);
     end
end

%function concore_write(port, name, val, delta)
%     global concore;
%     try
%         output1 = fopen(cat(2,concore.outpath, num2str(port), '/', name),"w");
%         outstr = cat(2,"[",num2str(concore.simtime),num2str(val,",%e"),"]");
%         fprintf(output1,'%s',outstr);
%         fclose(output1);
%     catch exc
%         disp(['skipping ' concore.outpath num2str(port) '/' name]);
%     end
%end
