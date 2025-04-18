classdef CodeGenerator < SwigRef
    %CODEGENERATOR Helper class for C code generation.
    %
    %
    %
    %Joel Andersson
    %
    %C++ includes: code_generator.hpp 
    %
  methods
    function this = swig_this(self)
      this = casadiMEX(3, self);
    end
    function self = CodeGenerator(varargin)
    %CODEGENERATOR Constructor.
    %
    %  new_obj = CODEGENERATOR()
    %
    %
    %
    %
      if nargin==1 && strcmp(class(varargin{1}),'SwigRef')
        if ~isnull(varargin{1})
          self.swigPtr = varargin{1}.swigPtr;
        end
      else
        tmp = casadiMEX(909, varargin{:});
        self.swigPtr = tmp.swigPtr;
        tmp.swigPtr = [];
      end
    end
    function varargout = add(self,varargin)
    %ADD Add a function (name generated)
    %
    %  ADD(self, Function f)
    %
    %
    %
    %
      [varargout{1:nargout}] = casadiMEX(910, self, varargin{:});
    end
    function varargout = dump(self,varargin)
    %DUMP Generate a file, return code as string.
    %
    %  char = DUMP(self)
    %
    %
    %
    %
      [varargout{1:nargout}] = casadiMEX(911, self, varargin{:});
    end
    function varargout = generate(self,varargin)
    %GENERATE Generate file(s) The "prefix" argument will be prepended to the generated
    %
    %  char = GENERATE(self, char prefix)
    %
    %files and may be a directory or a file prefix. returns the filename.
    %
    %
    %
      [varargout{1:nargout}] = casadiMEX(912, self, varargin{:});
    end
    function varargout = addInclude(self,varargin)
    %ADDINCLUDE Add an include file optionally using a relative path "..." instead of an
    %
    %  ADDINCLUDE(self, char new_include, bool relative_path, char use_ifdef)
    %
    %absolute path <...>
    %
    %
    %
      [varargout{1:nargout}] = casadiMEX(913, self, varargin{:});
    end
    function delete(self)
      if self.swigPtr
        casadiMEX(914, self);
        self.swigPtr=[];
      end
    end
  end
  methods(Static)
  end
end
