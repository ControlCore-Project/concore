% TestLiteralEvalMatlab.m
% Test suite for MATLAB/Octave Python-literal parser and serializer.
%
% Run in Octave: octave-cli TestLiteralEvalMatlab.m
% Run in MATLAB: matlab -batch "TestLiteralEvalMatlab"

passed = 0;
failed = 0;

function check(testName, condition)
    global passed failed;
    if condition
        fprintf('PASS: %s\n', testName);
        passed = passed + 1;
    else
        fprintf('FAIL: %s\n', testName);
        failed = failed + 1;
    end
end

function eq = approx(a, b)
    eq = abs(a - b) < 1e-9;
end

global passed failed;
passed = 0;
failed = 0;

fprintf('===== MATLAB/Octave Literal Parser & Serializer Tests =====\n\n');

% 1. Flat numeric list
v = concore_literal_eval('[10.0, 0.5, 2.3]');
check('flat_numeric size==3', numel(v) == 3);
check('flat_numeric[1]==10.0', approx(v(1), 10.0));
check('flat_numeric[2]==0.5', approx(v(2), 0.5));
check('flat_numeric[3]==2.3', approx(v(3), 2.3));

% 2. Empty list
v = concore_literal_eval('[]');
check('empty_list isempty', isempty(v));

% 3. Single element
v = concore_literal_eval('[42.0]');
check('single_element len==1', numel(v) == 1);
check('single_element[1]==42', approx(v(1), 42.0));

% 4. Negative numbers
v = concore_literal_eval('[-1.5, -3.0, 2.0]');
check('negative size==3', numel(v) == 3);
check('negative[1]==-1.5', approx(v(1), -1.5));
check('negative[2]==-3.0', approx(v(2), -3.0));

% 5. Scientific notation
v = concore_literal_eval('[1e3, 2.5E-2, -1.0e+1]');
check('sci size==3', numel(v) == 3);
check('sci[1]==1000', approx(v(1), 1000.0));
check('sci[2]==0.025', approx(v(2), 0.025));
check('sci[3]==-10', approx(v(3), -10.0));

% 6. Integer values
v = concore_literal_eval('[1, 2, 3]');
check('int size==3', numel(v) == 3);
check('int[1]==1', approx(v(1), 1.0));
check('int[3]==3', approx(v(3), 3.0));

% 7. String elements
v = concore_literal_eval('[10.0, "start", 0.5]');
check('string_elem iscell', iscell(v));
check('string_elem len==3', numel(v) == 3);
check('string_elem[1]==10.0', approx(v{1}, 10.0));
check('string_elem[2]=="start"', strcmp(v{2}, 'start'));
check('string_elem[3]==0.5', approx(v{3}, 0.5));

% 8. Boolean elements
v = concore_literal_eval('[True, False]');
check('bool iscell or array', numel(v) == 2);
if iscell(v)
    check('bool[1]==true', v{1} == true);
    check('bool[2]==false', v{2} == false);
else
    check('bool[1]==true', v(1) == true);
    check('bool[2]==false', v(2) == false);
end

% 9. Nested list
v = concore_literal_eval('[10.0, [0.5, 0.3], 0.1]');
check('nested iscell', iscell(v));
check('nested len==3', numel(v) == 3);
check('nested[1]==10.0', approx(v{1}, 10.0));
check('nested[2] is list', numel(v{2}) == 2);
if iscell(v{2})
    check('nested[2][1]==0.5', approx(v{2}{1}, 0.5));
    check('nested[2][2]==0.3', approx(v{2}{2}, 0.3));
else
    check('nested[2][1]==0.5', approx(v{2}(1), 0.5));
    check('nested[2][2]==0.3', approx(v{2}(2), 0.3));
end

% 10. Tuple payload
v = concore_literal_eval('(10.0, 0.3)');
check('tuple len==2', numel(v) == 2);
if iscell(v)
    check('tuple[1]==10.0', approx(v{1}, 10.0));
    check('tuple[2]==0.3', approx(v{2}, 0.3));
else
    check('tuple[1]==10.0', approx(v(1), 10.0));
    check('tuple[2]==0.3', approx(v(2), 0.3));
end

% 11. Escape sequences in string
v = concore_literal_eval('["line\none", "tab\ttwo"]');
check('escape newline', iscell(v) && strcmp(v{1}, sprintf('line\none')));
check('escape tab', iscell(v) && strcmp(v{2}, sprintf('tab\ttwo')));

% 12. Single-quoted strings
v = concore_literal_eval('[\''single_quote\'', 42]');
check('single_quote string', iscell(v) && strcmp(v{1}, 'single_quote'));

% 13. None literal
v = concore_literal_eval('[None, 1]');
check('none is empty', iscell(v) && isempty(v{1}));
check('none second elem is 1', iscell(v) && (v{2} == 1));

% 14. Dictionary parsing
v = concore_literal_eval('{"a": 1, "b": 2.5}');
check('dict is map', isa(v, 'containers.Map'));
check('dict has a', v('a') == 1);
check('dict has b', approx(v('b'), 2.5));

% 15. Serialization tests
s_num = concore_literal_serialize([1.0, 2.0, 3.0]);
check('serialize numeric contains 1', ~isempty(strfind(s_num, '1')));
check('serialize numeric contains 3', ~isempty(strfind(s_num, '3')));

s_bool = concore_literal_serialize(true);
check('serialize bool True', strcmp(s_bool, 'True'));

s_str = concore_literal_serialize('hello');
check('serialize string quotes', strcmp(s_str, '"hello"'));

s_cell = concore_literal_serialize({10.0, 'start', true, [1, 2]});
check('serialize cell starts with [', s_cell(1) == '[');
check('serialize cell contains start', ~isempty(strfind(s_cell, '"start"')));
check('serialize cell contains True', ~isempty(strfind(s_cell, 'True')));

fprintf('\n=== Results: %d passed, %d failed out of %d tests ===\n', passed, failed, passed + failed);
