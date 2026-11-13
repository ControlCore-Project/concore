function [str] = concore_literal_serialize(val)
% CONCORE_LITERAL_SERIALIZE Serializes MATLAB data types into a Python-literal string.
%
% Type mappings:
%   - double / single / int* (scalar) -> formatted numeric string (e.g. 1.5, -2)
%   - double / numeric vector/matrix -> [1.0, 2.0, 3.0] or nested [[...], [...]]
%   - logical (scalar)               -> True / False
%   - logical array                  -> [True, False, ...]
%   - char / string                  -> "..." with escaped quotes and control chars
%   - cell array                     -> [elem1, elem2, ...]
%   - containers.Map / struct        -> {'key1': val1, 'key2': val2}
%   - empty []                       -> []

    if isempty(val)
        str = '[]';
        return;
    end

    if islogical(val)
        if numel(val) == 1
            if val
                str = 'True';
            else
                str = 'False';
            end
        else
            items = cell(1, numel(val));
            for k = 1:numel(val)
                items{k} = concore_literal_serialize(val(k));
            end
            str = ['[', strjoin(items, ', '), ']'];
        end
    elseif isnumeric(val)
        if numel(val) == 1
            str = sprintf('%.17g', val);
        else
            sz = size(val);
            if sz(1) == 1 || sz(2) == 1
                % 1D vector
                items = cell(1, numel(val));
                for k = 1:numel(val)
                    items{k} = sprintf('%.17g', val(k));
                end
                str = ['[', strjoin(items, ', '), ']'];
            else
                % 2D matrix -> nested list of rows
                rows = cell(1, sz(1));
                for r = 1:sz(1)
                    row_items = cell(1, sz(2));
                    for c = 1:sz(2)
                        row_items{c} = sprintf('%.17g', val(r, c));
                    end
                    rows{r} = ['[', strjoin(row_items, ', '), ']'];
                end
                str = ['[', strjoin(rows, ', '), ']'];
            end
        end
    elseif ischar(val)
        escaped = strrep(val, '\', '\\');
        escaped = strrep(escaped, '"', '\"');
        escaped = strrep(escaped, sprintf('\n'), '\n');
        escaped = strrep(escaped, sprintf('\t'), '\t');
        escaped = strrep(escaped, sprintf('\r'), '\r');
        str = ['"', escaped, '"'];
    elseif isstring(val)
        if numel(val) == 1
            str = concore_literal_serialize(char(val));
        else
            items = cell(1, numel(val));
            for k = 1:numel(val)
                items{k} = concore_literal_serialize(char(val(k)));
            end
            str = ['[', strjoin(items, ', '), ']'];
        end
    elseif iscell(val)
        items = cell(1, numel(val));
        for k = 1:numel(val)
            items{k} = concore_literal_serialize(val{k});
        end
        str = ['[', strjoin(items, ', '), ']'];
    elseif isa(val, 'containers.Map')
        keys = val.keys();
        items = cell(1, numel(keys));
        for k = 1:numel(keys)
            k_str = concore_literal_serialize(keys{k});
            v_str = concore_literal_serialize(val(keys{k}));
            items{k} = [k_str, ': ', v_str];
        end
        str = ['{', strjoin(items, ', '), '}'];
    elseif isstruct(val)
        flds = fieldnames(val);
        items = cell(1, numel(flds));
        for k = 1:numel(flds)
            k_str = ['"', flds{k}, '"'];
            v_str = concore_literal_serialize(val.(flds{k}));
            items{k} = [k_str, ': ', v_str];
        end
        str = ['{', strjoin(items, ', '), '}'];
    else
        str = ['"', char(val), '"'];
    end
end
