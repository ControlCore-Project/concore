function test_literal_eval
    global concore;
    import_concore;

    % 1. Flat numeric list
    v = concore_literal_eval('[10.0, 0.5, 2.3]');
    assert(numel(v) == 3);
    assert(abs(v(1) - 10.0) < 1e-9);
    assert(abs(v(2) - 0.5) < 1e-9);
    assert(abs(v(3) - 2.3) < 1e-9);

    % 2. Empty list
    v = concore_literal_eval('[]');
    assert(isempty(v));

    % 3. Negative and scientific notation
    v = concore_literal_eval('[-1.5e2, 2.5E-2, -1.0e+1]');
    assert(numel(v) == 3);
    assert(abs(v(1) - (-150.0)) < 1e-9);
    assert(abs(v(2) - 0.025) < 1e-9);
    assert(abs(v(3) - (-10.0)) < 1e-9);

    % 4. Strings
    v = concore_literal_eval('[10.0, "start", ''sensor_a'']');
    assert(iscell(v));
    assert(numel(v) == 3);
    assert(abs(v{1} - 10.0) < 1e-9);
    assert(strcmp(v{2}, 'start'));
    assert(strcmp(v{3}, 'sensor_a'));

    % 5. Booleans
    v = concore_literal_eval('[True, False]');
    assert(numel(v) == 2);
    if iscell(v)
        assert(v{1} == true);
        assert(v{2} == false);
    else
        assert(v(1) == true);
        assert(v(2) == false);
    end

    % 6. Nested list
    v = concore_literal_eval('[10.0, [0.5, 0.3], 0.1]');
    assert(iscell(v));
    assert(numel(v) == 3);
    assert(abs(v{1} - 10.0) < 1e-9);
    if iscell(v{2})
        assert(abs(v{2}{1} - 0.5) < 1e-9);
        assert(abs(v{2}{2} - 0.3) < 1e-9);
    else
        assert(abs(v{2}(1) - 0.5) < 1e-9);
        assert(abs(v{2}(2) - 0.3) < 1e-9);
    end

    % 7. Serialization round-trip
    s_cell = concore_literal_serialize({10.0, 'start', true, [1.0, 2.0]});
    v_back = concore_literal_eval(s_cell);
    assert(iscell(v_back));
    assert(abs(v_back{1} - 10.0) < 1e-9);
    assert(strcmp(v_back{2}, 'start'));
    assert(v_back{3} == true);

    % 8. concore_initval test
    res = concore_initval('[5.0, 1.2, 3.4]');
    assert(abs(concore.simtime - 5.0) < 1e-9);
    assert(numel(res) == 2);
    assert(abs(res(1) - 1.2) < 1e-9);
    assert(abs(res(2) - 3.4) < 1e-9);

    disp('All MATLAB literal eval and wire-format tests passed successfully!');
end
