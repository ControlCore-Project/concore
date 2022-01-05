function [result] = concore_unchanged()
     global concore;
     %disp("s=")
     %disp(s)
     %disp("olds=")
     %disp(olds)
     if isequal(concore.olds,concore.s)
        concore.s = '';
        result = 1;
       % disp("true")
     else
        concore.olds = concore.s;
        result = 0;
       % disp("false")
     end
end