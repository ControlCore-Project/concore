function test_julia_interop
    global concore;
    import_concore;

    interop_dir = getenv('CONCORE_INTEROP_DIR');
    assert(~isempty(interop_dir));

    concore.delay = 0;
    concore.inpath = fullfile(interop_dir, 'julia_out');

    result = concore_read(1, 'signal', '[0.0, 0.0, 0.0]');
    assert(all(abs(result - [21.0, 22.5]) < 1e-9));
    assert(abs(concore.simtime - 12.0) < 1e-9);

    concore.outpath = fullfile(interop_dir, 'matlab_out');
    output_dir = [concore.outpath '1'];
    if exist(output_dir, 'dir') ~= 7
        mkdir(output_dir);
    end
    concore.simtime = 14.0;
    concore_write(1, 'signal', [31.0, 32.5], 0);
    assert(exist(fullfile(output_dir, 'signal'), 'file') == 2);
end
