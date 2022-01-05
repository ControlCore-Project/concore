function [u, x0, Pd] = MPC(u, x0, ym, Data, Pd)
% Current values of input and output
    yp = ym - Data.op1.ysp;
    up = u - Data.op1.us;
% Measurement update
    M = Pd*Data.op1.C'/(Data.op1.C*Pd*Data.op1.C' + Data.input.Rd);
    x_0 = x0 + M*(yp - Data.op1.C*x0 - Data.op1.D*up);
    Pd = Data.op1.A*(Pd - M*Data.op1.C*Pd)*Data.op1.A'+ Data.op1.K*Data.input.Qd*Data.op1.K';
% Quadratic Objective Function matrices: H= w'*alpha*w + beta + Z'*gamma*Z; 
%                                        f= W'alpha'Vx_0;
    H = Data.op1.W'*Data.op1.alpha*Data.op1.W + Data.op1.beta + Data.op1.Z'*Data.op1.gamma*Data.op1.Z;
    H = (H + H')/2;
    f = Data.op1.W'*Data.op1.alpha'*Data.op1.V*x_0;
% linear inequality constraint
    A = [eye(Data.input.Nu*(Data.input.Np-1)); -eye(Data.input.Nu*(Data.input.Np-1)); Data.op1.G*Data.op1.W + Data.op1.J; -Data.op1.G*Data.op1.W - Data.op1.J];
    b = [Data.input.Umax - Data.op1.Us; -(Data.input.Umin - Data.op1.Us); Data.output.Ymax - Data.op1.Ys - Data.op1.G*Data.op1.V*x_0; -(Data.output.Ymin - Data.op1.Ys) + Data.op1.G*Data.op1.V*x_0]; 
% Solve the quadratic problem     
    options = optimoptions(@quadprog,'Display', 'none', 'MaxIter', 1000);
    [U,~,flag] = quadprog(H,f,A,b,[],[],[],[],[],options);
    disp(['            Optimization Flag: ' num2str(flag)])
% Next Cycle's Inputs:
    if flag == 1
        u = U(1:Data.input.Nu)+ Data.op1.us;
    else
        u = u;
    end
    x0 = Data.op1.A*x_0 + Data.op1.B*up;
end