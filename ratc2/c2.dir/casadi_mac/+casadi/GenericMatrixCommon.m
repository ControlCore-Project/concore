classdef GenericMatrixCommon < SwigRef
    %GENERICMATRIXCOMMON 
    %
    %   = GENERICMATRIXCOMMON()
    %
    %
  methods
    function this = swig_this(self)
      this = casadiMEX(3, self);
    end

    function varargout = subsref(self,s)
      if numel(s)==1 && strcmp(s.type,'()')
        [varargout{1}] = paren(self, s.subs{:});
      elseif numel(s)==1 && strcmp(s.type,'{}')
        [varargout{1}] = brace(self, s.subs{:});
      else
        [varargout{1:nargout}] = builtin('subsref',self,s);
      end
    end
    function self = subsasgn(self,s,v)
      if numel(s)==1 && strcmp(s.type,'()')
        paren_asgn(self, v, s.subs{:});
      elseif numel(s)==1 && strcmp(s.type,'{}')
        brace_asgn(self, v, s.subs{:});
      else
        self = builtin('subsasgn',self,s,v);
      end
    end
    function out = sum(self,varargin)
      narginchk(1,2);
      if nargin==1
        if is_vector(self)
          if is_column(self)
            out = sum1(self);
          else
            out = sum2(self);
          end
        else
          out = sum1(self);
        end
      else
        i = varargin{1};
        if i==1
          out = sum1(self);
        elseif i==2
          out = sum2(self);
        else
          error('sum argument (if present) must be 1 or 2');
        end
      end
    end
    function out = norm(self,varargin)
      narginchk(1,2);
      % 2-norm by default
      if nargin==1
        ind = 2;
      else
        ind = varargin{1};
      end
      % Typecheck
      assert((isnumeric(ind) && isscalar(ind)) || ischar(ind))
      % Pick the right norm
      if isnumeric(ind)
        switch ind
          case 1
            out = norm_1(self);
          case 2
            out = norm_2(self);
          case inf
            out = norm_inf(self);
          otherwise
            error(sprintf('Unknown norm argument: %g', ind))
        end
      else
        switch ind
          case 'fro'
            out = norm_fro(self);
          case 'inf'
            out = norm_inf(self);
          otherwise
            error(sprintf('Unknown norm argument: ''%s''', ind))
        end
      end
    end
    function b = isrow(self)
      b = is_row(self);
    end
    function b = iscolumn(self)
      b = is_column(self);
    end
    function b = isvector(self)
      b = is_vector(self);
    end
    function b = isscalar(self)
      b = is_scalar(self);
    end
      function varargout = mpower(varargin)
    %MPOWER 
    %
    %  IM = MPOWER(IM x, IM n)
    %  DM = MPOWER(DM x, DM n)
    %  SX = MPOWER(SX x, SX n)
    %  MX = MPOWER(MX x, MX n)
    %
    %
     [varargout{1:nargout}] = casadiMEX(204, varargin{:});
    end
    function varargout = mrdivide(varargin)
    %MRDIVIDE 
    %
    %  IM = MRDIVIDE(IM x, IM y)
    %  DM = MRDIVIDE(DM x, DM y)
    %  SX = MRDIVIDE(SX x, SX y)
    %  MX = MRDIVIDE(MX x, MX y)
    %
    %
     [varargout{1:nargout}] = casadiMEX(205, varargin{:});
    end
    function varargout = mldivide(varargin)
    %MLDIVIDE 
    %
    %  IM = MLDIVIDE(IM x, IM y)
    %  DM = MLDIVIDE(DM x, DM y)
    %  SX = MLDIVIDE(SX x, SX y)
    %  MX = MLDIVIDE(MX x, MX y)
    %
    %
     [varargout{1:nargout}] = casadiMEX(206, varargin{:});
    end
    function varargout = symvar(varargin)
    %SYMVAR 
    %
    %  {IM} = SYMVAR(IM x)
    %  {DM} = SYMVAR(DM x)
    %  {SX} = SYMVAR(SX x)
    %  {MX} = SYMVAR(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(207, varargin{:});
    end
    function varargout = bilin(varargin)
    %BILIN 
    %
    %  IM = BILIN(IM A, IM x, IM y)
    %  DM = BILIN(DM A, DM x, DM y)
    %  SX = BILIN(SX A, SX x, SX y)
    %  MX = BILIN(MX A, MX x, MX y)
    %
    %
     [varargout{1:nargout}] = casadiMEX(208, varargin{:});
    end
    function varargout = rank1(varargin)
    %RANK1 
    %
    %  IM = RANK1(IM A, IM alpha, IM x, IM y)
    %  DM = RANK1(DM A, DM alpha, DM x, DM y)
    %  SX = RANK1(SX A, SX alpha, SX x, SX y)
    %  MX = RANK1(MX A, MX alpha, MX x, MX y)
    %
    %
     [varargout{1:nargout}] = casadiMEX(209, varargin{:});
    end
    function varargout = sum_square(varargin)
    %SUM_SQUARE 
    %
    %  IM = SUM_SQUARE(IM X)
    %  DM = SUM_SQUARE(DM X)
    %  SX = SUM_SQUARE(SX X)
    %  MX = SUM_SQUARE(MX X)
    %
    %
     [varargout{1:nargout}] = casadiMEX(210, varargin{:});
    end
    function varargout = linspace(varargin)
    %LINSPACE 
    %
    %  IM = LINSPACE(IM a, IM b, int nsteps)
    %  DM = LINSPACE(DM a, DM b, int nsteps)
    %  SX = LINSPACE(SX a, SX b, int nsteps)
    %  MX = LINSPACE(MX a, MX b, int nsteps)
    %
    %
     [varargout{1:nargout}] = casadiMEX(211, varargin{:});
    end
    function varargout = cross(varargin)
    %CROSS 
    %
    %  IM = CROSS(IM a, IM b, int dim)
    %  DM = CROSS(DM a, DM b, int dim)
    %  SX = CROSS(SX a, SX b, int dim)
    %  MX = CROSS(MX a, MX b, int dim)
    %
    %
     [varargout{1:nargout}] = casadiMEX(212, varargin{:});
    end
    function varargout = skew(varargin)
    %SKEW 
    %
    %  IM = SKEW(IM a)
    %  DM = SKEW(DM a)
    %  SX = SKEW(SX a)
    %  MX = SKEW(MX a)
    %
    %
     [varargout{1:nargout}] = casadiMEX(213, varargin{:});
    end
    function varargout = inv_skew(varargin)
    %INV_SKEW 
    %
    %  IM = INV_SKEW(IM a)
    %  DM = INV_SKEW(DM a)
    %  SX = INV_SKEW(SX a)
    %  MX = INV_SKEW(MX a)
    %
    %
     [varargout{1:nargout}] = casadiMEX(214, varargin{:});
    end
    function varargout = det(varargin)
    %DET 
    %
    %  IM = DET(IM A)
    %  DM = DET(DM A)
    %  SX = DET(SX A)
    %  MX = DET(MX A)
    %
    %
     [varargout{1:nargout}] = casadiMEX(215, varargin{:});
    end
    function varargout = inv(varargin)
    %INV 
    %
    %  IM = INV(IM A)
    %  DM = INV(DM A)
    %  SX = INV(SX A)
    %  MX = INV(MX A)
    %
    %
     [varargout{1:nargout}] = casadiMEX(216, varargin{:});
    end
    function varargout = trace(varargin)
    %TRACE 
    %
    %  IM = TRACE(IM a)
    %  DM = TRACE(DM a)
    %  SX = TRACE(SX a)
    %  MX = TRACE(MX a)
    %
    %
     [varargout{1:nargout}] = casadiMEX(217, varargin{:});
    end
    function varargout = tril2symm(varargin)
    %TRIL2SYMM 
    %
    %  IM = TRIL2SYMM(IM a)
    %  DM = TRIL2SYMM(DM a)
    %  SX = TRIL2SYMM(SX a)
    %  MX = TRIL2SYMM(MX a)
    %
    %
     [varargout{1:nargout}] = casadiMEX(218, varargin{:});
    end
    function varargout = triu2symm(varargin)
    %TRIU2SYMM 
    %
    %  IM = TRIU2SYMM(IM a)
    %  DM = TRIU2SYMM(DM a)
    %  SX = TRIU2SYMM(SX a)
    %  MX = TRIU2SYMM(MX a)
    %
    %
     [varargout{1:nargout}] = casadiMEX(219, varargin{:});
    end
    function varargout = norm_fro(varargin)
    %NORM_FRO 
    %
    %  IM = NORM_FRO(IM x)
    %  DM = NORM_FRO(DM x)
    %  SX = NORM_FRO(SX x)
    %  MX = NORM_FRO(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(220, varargin{:});
    end
    function varargout = norm_2(varargin)
    %NORM_2 
    %
    %  IM = NORM_2(IM x)
    %  DM = NORM_2(DM x)
    %  SX = NORM_2(SX x)
    %  MX = NORM_2(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(221, varargin{:});
    end
    function varargout = norm_1(varargin)
    %NORM_1 
    %
    %  IM = NORM_1(IM x)
    %  DM = NORM_1(DM x)
    %  SX = NORM_1(SX x)
    %  MX = NORM_1(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(222, varargin{:});
    end
    function varargout = norm_inf(varargin)
    %NORM_INF 
    %
    %  IM = NORM_INF(IM x)
    %  DM = NORM_INF(DM x)
    %  SX = NORM_INF(SX x)
    %  MX = NORM_INF(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(223, varargin{:});
    end
    function varargout = sum2(varargin)
    %SUM2 
    %
    %  IM = SUM2(IM x)
    %  DM = SUM2(DM x)
    %  SX = SUM2(SX x)
    %  MX = SUM2(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(224, varargin{:});
    end
    function varargout = sum1(varargin)
    %SUM1 
    %
    %  IM = SUM1(IM x)
    %  DM = SUM1(DM x)
    %  SX = SUM1(SX x)
    %  MX = SUM1(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(225, varargin{:});
    end
    function varargout = dot(varargin)
    %DOT 
    %
    %  IM = DOT(IM x, IM y)
    %  DM = DOT(DM x, DM y)
    %  SX = DOT(SX x, SX y)
    %  MX = DOT(MX x, MX y)
    %
    %
     [varargout{1:nargout}] = casadiMEX(226, varargin{:});
    end
    function varargout = nullspace(varargin)
    %NULLSPACE 
    %
    %  IM = NULLSPACE(IM A)
    %  DM = NULLSPACE(DM A)
    %  SX = NULLSPACE(SX A)
    %  MX = NULLSPACE(MX A)
    %
    %
     [varargout{1:nargout}] = casadiMEX(227, varargin{:});
    end
    function varargout = polyval(varargin)
    %POLYVAL 
    %
    %  IM = POLYVAL(IM p, IM x)
    %  DM = POLYVAL(DM p, DM x)
    %  SX = POLYVAL(SX p, SX x)
    %  MX = POLYVAL(MX p, MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(228, varargin{:});
    end
    function varargout = diag(varargin)
    %DIAG 
    %
    %  IM = DIAG(IM A)
    %  DM = DIAG(DM A)
    %  SX = DIAG(SX A)
    %  MX = DIAG(MX A)
    %
    %
     [varargout{1:nargout}] = casadiMEX(229, varargin{:});
    end
    function varargout = unite(varargin)
    %UNITE 
    %
    %  IM = UNITE(IM A, IM B)
    %  DM = UNITE(DM A, DM B)
    %  SX = UNITE(SX A, SX B)
    %  MX = UNITE(MX A, MX B)
    %
    %
     [varargout{1:nargout}] = casadiMEX(230, varargin{:});
    end
    function varargout = densify(varargin)
    %DENSIFY 
    %
    %  IM = DENSIFY(IM x)
    %  DM = DENSIFY(DM x)
    %  SX = DENSIFY(SX x)
    %  MX = DENSIFY(MX x)
    %
    %
     [varargout{1:nargout}] = casadiMEX(231, varargin{:});
    end
    function varargout = project(varargin)
    %PROJECT 
    %
    %  IM = PROJECT(IM A, Sparsity sp, bool intersect)
    %  DM = PROJECT(DM A, Sparsity sp, bool intersect)
    %  SX = PROJECT(SX A, Sparsity sp, bool intersect)
    %  MX = PROJECT(MX A, Sparsity sp, bool intersect)
    %
    %
     [varargout{1:nargout}] = casadiMEX(232, varargin{:});
    end
    function varargout = if_else(varargin)
    %IF_ELSE 
    %
    %  IM = IF_ELSE(IM cond, IM if_true, IM if_false, bool short_circuit)
    %  DM = IF_ELSE(DM cond, DM if_true, DM if_false, bool short_circuit)
    %  SX = IF_ELSE(SX cond, SX if_true, SX if_false, bool short_circuit)
    %  MX = IF_ELSE(MX cond, MX if_true, MX if_false, bool short_circuit)
    %
    %
     [varargout{1:nargout}] = casadiMEX(233, varargin{:});
    end
    function varargout = conditional(varargin)
    %CONDITIONAL 
    %
    %  IM = CONDITIONAL(IM ind, {IM} x, IM x_default, bool short_circuit)
    %  DM = CONDITIONAL(DM ind, {DM} x, DM x_default, bool short_circuit)
    %  SX = CONDITIONAL(SX ind, {SX} x, SX x_default, bool short_circuit)
    %  MX = CONDITIONAL(MX ind, {MX} x, MX x_default, bool short_circuit)
    %
    %
     [varargout{1:nargout}] = casadiMEX(234, varargin{:});
    end
    function varargout = depends_on(varargin)
    %DEPENDS_ON 
    %
    %  bool = DEPENDS_ON(IM f, IM arg)
    %  bool = DEPENDS_ON(DM f, DM arg)
    %  bool = DEPENDS_ON(SX f, SX arg)
    %  bool = DEPENDS_ON(MX f, MX arg)
    %
    %
     [varargout{1:nargout}] = casadiMEX(235, varargin{:});
    end
    function varargout = solve(varargin)
    %SOLVE 
    %
    %  IM = SOLVE(IM A, IM b)
    %  DM = SOLVE(DM A, DM b)
    %  SX = SOLVE(SX A, SX b)
    %  MX = SOLVE(MX A, MX b)
    %  IM = SOLVE(IM A, IM b, char lsolver, struct opts)
    %  DM = SOLVE(DM A, DM b, char lsolver, struct opts)
    %  SX = SOLVE(SX A, SX b, char lsolver, struct opts)
    %  MX = SOLVE(MX A, MX b, char lsolver, struct opts)
    %
    %
     [varargout{1:nargout}] = casadiMEX(236, varargin{:});
    end
    function varargout = pinv(varargin)
    %PINV 
    %
    %  IM = PINV(IM A)
    %  DM = PINV(DM A)
    %  SX = PINV(SX A)
    %  MX = PINV(MX A)
    %  IM = PINV(IM A, char lsolver, struct opts)
    %  DM = PINV(DM A, char lsolver, struct opts)
    %  SX = PINV(SX A, char lsolver, struct opts)
    %  MX = PINV(MX A, char lsolver, struct opts)
    %
    %
     [varargout{1:nargout}] = casadiMEX(237, varargin{:});
    end
    function varargout = expm_const(varargin)
    %EXPM_CONST 
    %
    %  IM = EXPM_CONST(IM A, IM t)
    %  DM = EXPM_CONST(DM A, DM t)
    %  SX = EXPM_CONST(SX A, SX t)
    %  MX = EXPM_CONST(MX A, MX t)
    %
    %
     [varargout{1:nargout}] = casadiMEX(238, varargin{:});
    end
    function varargout = expm(varargin)
    %EXPM 
    %
    %  IM = EXPM(IM A)
    %  DM = EXPM(DM A)
    %  SX = EXPM(SX A)
    %  MX = EXPM(MX A)
    %
    %
     [varargout{1:nargout}] = casadiMEX(239, varargin{:});
    end
    function varargout = jacobian(varargin)
    %JACOBIAN 
    %
    %  IM = JACOBIAN(IM ex, IM arg, struct opts)
    %  DM = JACOBIAN(DM ex, DM arg, struct opts)
    %  SX = JACOBIAN(SX ex, SX arg, struct opts)
    %  MX = JACOBIAN(MX ex, MX arg, struct opts)
    %
    %
     [varargout{1:nargout}] = casadiMEX(240, varargin{:});
    end
    function varargout = jtimes(varargin)
    %JTIMES 
    %
    %  IM = JTIMES(IM ex, IM arg, IM v, bool tr)
    %  DM = JTIMES(DM ex, DM arg, DM v, bool tr)
    %  SX = JTIMES(SX ex, SX arg, SX v, bool tr)
    %  MX = JTIMES(MX ex, MX arg, MX v, bool tr)
    %
    %
     [varargout{1:nargout}] = casadiMEX(241, varargin{:});
    end
    function varargout = linearize(varargin)
    %LINEARIZE 
    %
    %  IM = LINEARIZE(IM f, IM x, IM x0)
    %  DM = LINEARIZE(DM f, DM x, DM x0)
    %  SX = LINEARIZE(SX f, SX x, SX x0)
    %  MX = LINEARIZE(MX f, MX x, MX x0)
    %
    %
     [varargout{1:nargout}] = casadiMEX(242, varargin{:});
    end
    function varargout = which_depends(varargin)
    %WHICH_DEPENDS 
    %
    %  [bool] = WHICH_DEPENDS(IM expr, IM var, int order, bool tr)
    %  [bool] = WHICH_DEPENDS(DM expr, DM var, int order, bool tr)
    %  [bool] = WHICH_DEPENDS(SX expr, SX var, int order, bool tr)
    %  [bool] = WHICH_DEPENDS(MX expr, MX var, int order, bool tr)
    %
    %
     [varargout{1:nargout}] = casadiMEX(243, varargin{:});
    end
    function varargout = gradient(varargin)
    %GRADIENT 
    %
    %  IM = GRADIENT(IM ex, IM arg)
    %  DM = GRADIENT(DM ex, DM arg)
    %  SX = GRADIENT(SX ex, SX arg)
    %  MX = GRADIENT(MX ex, MX arg)
    %
    %
     [varargout{1:nargout}] = casadiMEX(244, varargin{:});
    end
    function varargout = tangent(varargin)
    %TANGENT 
    %
    %  IM = TANGENT(IM ex, IM arg)
    %  DM = TANGENT(DM ex, DM arg)
    %  SX = TANGENT(SX ex, SX arg)
    %  MX = TANGENT(MX ex, MX arg)
    %
    %
     [varargout{1:nargout}] = casadiMEX(245, varargin{:});
    end
    function varargout = hessian(varargin)
    %HESSIAN 
    %
    %  [IM , IM OUTPUT1] = HESSIAN(IM ex, IM arg)
    %  [DM , DM OUTPUT1] = HESSIAN(DM ex, DM arg)
    %  [SX , SX OUTPUT1] = HESSIAN(SX ex, SX arg)
    %  [MX , MX OUTPUT1] = HESSIAN(MX ex, MX arg)
    %
    %
     [varargout{1:nargout}] = casadiMEX(246, varargin{:});
    end
    function varargout = n_nodes(varargin)
    %N_NODES 
    %
    %  int = N_NODES(IM A)
    %  int = N_NODES(DM A)
    %  int = N_NODES(SX A)
    %  int = N_NODES(MX A)
    %
    %
     [varargout{1:nargout}] = casadiMEX(247, varargin{:});
    end
    function varargout = print_operator(varargin)
    %PRINT_OPERATOR 
    %
    %  char = PRINT_OPERATOR(IM xb, [char] args)
    %  char = PRINT_OPERATOR(DM xb, [char] args)
    %  char = PRINT_OPERATOR(SX xb, [char] args)
    %  char = PRINT_OPERATOR(MX xb, [char] args)
    %
    %
     [varargout{1:nargout}] = casadiMEX(248, varargin{:});
    end
    function varargout = repsum(varargin)
    %REPSUM 
    %
    %  IM = REPSUM(IM A, int n, int m)
    %  DM = REPSUM(DM A, int n, int m)
    %  SX = REPSUM(SX A, int n, int m)
    %  MX = REPSUM(MX A, int n, int m)
    %
    %
     [varargout{1:nargout}] = casadiMEX(249, varargin{:});
    end
    function varargout = einstein(varargin)
    %EINSTEIN 
    %
    %  IM = EINSTEIN(IM A, IM B, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %  DM = EINSTEIN(DM A, DM B, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %  SX = EINSTEIN(SX A, SX B, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %  MX = EINSTEIN(MX A, MX B, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %  IM = EINSTEIN(IM A, IM B, IM C, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %  DM = EINSTEIN(DM A, DM B, DM C, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %  SX = EINSTEIN(SX A, SX B, SX C, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %  MX = EINSTEIN(MX A, MX B, MX C, [int] dim_a, [int] dim_b, [int] dim_c, [int] a, [int] b, [int] c)
    %
    %
     [varargout{1:nargout}] = casadiMEX(250, varargin{:});
    end
    function self = GenericMatrixCommon(varargin)
    %GENERICMATRIXCOMMON 
    %
    %  new_obj = GENERICMATRIXCOMMON()
    %
    %
      if nargin==1 && strcmp(class(varargin{1}),'SwigRef')
        if ~isnull(varargin{1})
          self.swigPtr = varargin{1}.swigPtr;
        end
      else
        tmp = casadiMEX(251, varargin{:});
        self.swigPtr = tmp.swigPtr;
        tmp.swigPtr = [];
      end
    end
    function delete(self)
      if self.swigPtr
        casadiMEX(252, self);
        self.swigPtr=[];
      end
    end
  end
  methods(Static)
  end
end
