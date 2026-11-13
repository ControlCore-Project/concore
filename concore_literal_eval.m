function [val] = concore_literal_eval(str)
% CONCORE_LITERAL_EVAL Parses a Python-literal-formatted payload into MATLAB types.
%
% Supported grammar:
%   - Numbers: integers, floating point, scientific notation (e.g. 10.0, -1.5, 1e3, 2.5E-2)
%   - Booleans: True -> true (logical), False -> false (logical)
%   - None: None -> []
%   - Strings: '...' or "..." with escape sequence support (\n, \t, \r, \\, \', \")
%   - Lists: [...] -> cell array or numeric array
%   - Tuples: (...) -> cell array or numeric array (identical to lists)
%   - Dictionaries: {...} -> containers.Map
%
% Examples:
%   concore_literal_eval('[10.0, 0.5, 2.3]')               -> [10.0, 0.5, 2.3]
%   concore_literal_eval('[10.0, "start", True, [1, 2]]') -> {10.0, 'start', true, [1, 2]}

    if ~ischar(str)
        if isstring(str)
            str = char(str);
        else
            val = str;
            return;
        end
    end

    str = strtrim(str);
    if isempty(str)
        val = [];
        return;
    end

    [val, pos] = parse_value(str, 1);
end

function [val, p] = parse_value(s, p)
    p = skip_ws(s, p);
    n = length(s);
    if p > n
        val = [];
        return;
    end

    c = s(p);
    if c == '[' || c == '('
        [val, p] = parse_array(s, p);
    elseif c == '{'
        [val, p] = parse_dict(s, p);
    elseif c == '''' || c == '"'
        [val, p] = parse_string(s, p);
    else
        [val, p] = parse_atom(s, p);
    end
end

function [res, p] = parse_array(s, p)
    open_char = s(p);
    if open_char == '['
        close_char = ']';
    else
        close_char = ')';
    end
    p = p + 1;
    n = length(s);
    elements = {};
    p = skip_ws(s, p);

    if p <= n && s(p) == close_char
        p = p + 1;
        res = {};
        return;
    end

    while p <= n
        [elem, p] = parse_value(s, p);
        elements{end+1} = elem;
        p = skip_ws(s, p);

        if p <= n && s(p) == ','
            p = p + 1;
            p = skip_ws(s, p);
        end

        if p <= n && s(p) == close_char
            p = p + 1;
            % If all elements are numeric scalars, simplify to standard numeric array
            all_num_scalar = true;
            for k = 1:numel(elements)
                if ~isnumeric(elements{k}) || numel(elements{k}) ~= 1
                    all_num_scalar = false;
                    break;
                end
            end
            if all_num_scalar && ~isempty(elements)
                res = cell2mat(elements);
            else
                res = elements;
            end
            return;
        end
    end

    error('concore:parse_error', 'Unterminated array or tuple');
end

function [res, p] = parse_dict(s, p)
    p = p + 1; % Skip '{'
    n = length(s);
    res = containers.Map();
    p = skip_ws(s, p);

    if p <= n && s(p) == '}'
        p = p + 1;
        return;
    end

    while p <= n
        [k_val, p] = parse_value(s, p);
        p = skip_ws(s, p);
        if p > n || s(p) ~= ':'
            error('concore:parse_error', 'Expected ":" in dictionary');
        end
        p = p + 1; % Skip ':'
        [v_val, p] = parse_value(s, p);

        if ischar(k_val)
            key_str = k_val;
        else
            key_str = num2str(k_val);
        end
        res(key_str) = v_val;

        p = skip_ws(s, p);
        if p <= n && s(p) == ','
            p = p + 1;
            p = skip_ws(s, p);
        end

        if p <= n && s(p) == '}'
            p = p + 1;
            return;
        end
    end

    error('concore:parse_error', 'Unterminated dictionary');
end

function [res, p] = parse_string(s, p)
    quote = s(p);
    p = p + 1;
    n = length(s);
    buf = '';

    while p <= n && s(p) ~= quote
        if s(p) == '\' && p < n
            p = p + 1;
            esc = s(p);
            switch esc
                case 'n'
                    buf = [buf, sprintf('\n')];
                case 't'
                    buf = [buf, sprintf('\t')];
                case 'r'
                    buf = [buf, sprintf('\r')];
                case '\'
                    buf = [buf, '\'];
                case ''''
                    buf = [buf, ''''];
                case '"'
                    buf = [buf, '"'];
                otherwise
                    buf = [buf, '\', esc];
            end
        else
            buf = [buf, s(p)];
        end
        p = p + 1;
    end

    if p > n
        error('concore:parse_error', 'Unterminated string literal');
    end

    p = p + 1; % Skip closing quote
    res = buf;
end

function [res, p] = parse_atom(s, p)
    n = length(s);

    % Boolean: True
    if p + 3 <= n && strcmp(s(p:p+3), 'True') && (p + 4 > n || ~is_id_char(s(p+4)))
        res = true;
        p = p + 4;
        return;
    end

    % Boolean: False
    if p + 4 <= n && strcmp(s(p:p+4), 'False') && (p + 5 > n || ~is_id_char(s(p+5)))
        res = false;
        p = p + 5;
        return;
    end

    % None
    if p + 3 <= n && strcmp(s(p:p+3), 'None') && (p + 4 > n || ~is_id_char(s(p+4)))
        res = [];
        p = p + 4;
        return;
    end

    % Number parsing
    start_p = p;
    while p <= n && s(p) ~= ' ' && s(p) ~= sprintf('\t') && s(p) ~= sprintf('\n') && ...
          s(p) ~= sprintf('\r') && s(p) ~= ',' && s(p) ~= ']' && s(p) ~= ')' && ...
          s(p) ~= '}' && s(p) ~= ':'
        p = p + 1;
    end

    num_str = s(start_p:p-1);
    num_val = str2double(num_str);
    if isnan(num_val) && ~strcmpi(num_str, 'nan')
        error('concore:parse_error', sprintf('Invalid token: %s', num_str));
    end
    res = num_val;
end

function p = skip_ws(s, p)
    n = length(s);
    while p <= n && (s(p) == ' ' || s(p) == sprintf('\t') || s(p) == sprintf('\n') || s(p) == sprintf('\r'))
        p = p + 1;
    end
end

function b = is_id_char(c)
    b = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_';
end
