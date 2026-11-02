function test_write_advance
    % issue #608: concore_write leaves simtime alone, the next read moves it
    % forward so a node whose own writes are its clock still reaches maxtime
    global concore;
    import_concore;

    dir = tempname;
    mkdir(dir);
    mkdir(fullfile(dir, 'in1'));
    mkdir(fullfile(dir, 'out1'));
    concore.inpath = [dir '/in'];
    concore.outpath = [dir '/out'];
    concore.delay = 0;

    % 1. one write, then a read that gets no newer timestamp
    concore.simtime = 10;
    concore_write(1, 'u', [1.0], 1);
    assert(concore.simtime == 10);
    concore_read(1, 'missing', '[0.0, 5.0]');
    assert(concore.simtime == 11);

    % 2. several writes in one step advance it once, to the largest delta
    concore.simtime = 20;
    concore_write(1, 'u', [1.0], 1);
    concore_write(1, 'v', [2.0], 2);
    concore_read(1, 'missing', '[0.0, 5.0]');
    assert(concore.simtime == 22);

    % 3. simtime set by hand after the write wins
    concore.simtime = 30;
    concore_write(1, 'u', [1.0], 1);
    concore.simtime = 3;
    concore_read(1, 'missing', '[0.0, 5.0]');
    assert(concore.simtime == 3);

    rmdir(dir, 's');
    disp('MATLAB write advance tests passed');
end
