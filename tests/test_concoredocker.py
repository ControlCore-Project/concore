import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import concoredocker

def test_safe_literal_eval_dict():
    f = tempfile.NamedTemporaryFile(mode='w', delete=False)
    f.write("{'a': 1, 'b': 2}")
    f.close()
    result = concoredocker.safe_literal_eval(f.name, {})
    os.unlink(f.name)
    assert result == {'a': 1, 'b': 2}

def test_safe_literal_eval_list():
    f = tempfile.NamedTemporaryFile(mode='w', delete=False)
    f.write("[1, 2, 3]")
    f.close()
    result = concoredocker.safe_literal_eval(f.name, [])
    os.unlink(f.name)
    assert result == [1, 2, 3]

def test_safe_literal_eval_missing():
    result = concoredocker.safe_literal_eval("/nonexistent.txt", {'default': True})
    assert result == {'default': True}

def test_safe_literal_eval_bad_syntax():
    f = tempfile.NamedTemporaryFile(mode='w', delete=False)
    f.write("not valid {{{")
    f.close()
    result = concoredocker.safe_literal_eval(f.name, "fallback")
    os.unlink(f.name)
    assert result == "fallback"

def test_initval():
    concoredocker.simtime = 0
    result = concoredocker.initval("[5.0, 1.0, 2.0]")
    assert result == [1.0, 2.0]
    assert concoredocker.simtime == 5.0

def test_initval_single():
    concoredocker.simtime = 0
    result = concoredocker.initval("[10.0, 99]")
    assert result == [99]
    assert concoredocker.simtime == 10.0

def test_unchanged_true():
    concoredocker.s = "abc"
    concoredocker.olds = "abc"
    assert concoredocker.unchanged() == True
    assert concoredocker.s == ''

def test_unchanged_false():
    concoredocker.s = "new"
    concoredocker.olds = "old"
    assert concoredocker.unchanged() == False
    assert concoredocker.olds == "new"

def test_write_list():
    tmpdir = tempfile.mkdtemp()
    outdir = os.path.join(tmpdir, "out1")
    os.makedirs(outdir)
    old_outpath = concoredocker.outpath
    concoredocker.outpath = os.path.join(tmpdir, "out")
    concoredocker.simtime = 5.0
    
    concoredocker.write(1, "testfile", [1.0, 2.0], delta=0)
    
    with open(os.path.join(outdir, "testfile")) as f:
        content = f.read()
    assert content == "[5.0, 1.0, 2.0]"
    concoredocker.outpath = old_outpath
    
def test_write_delta():
    tmpdir = tempfile.mkdtemp()
    outdir = os.path.join(tmpdir, "out1")
    os.makedirs(outdir)
    old_outpath = concoredocker.outpath
    concoredocker.outpath = os.path.join(tmpdir, "out")
    concoredocker.simtime = 10.0
    
    concoredocker.write(1, "testfile", [3.0], delta=2)
    
    with open(os.path.join(outdir, "testfile")) as f:
        content = f.read()
    assert content == "[12.0, 3.0]"
    assert concoredocker.simtime == 12.0
    concoredocker.outpath = old_outpath

def test_read_file():
    tmpdir = tempfile.mkdtemp()
    indir = os.path.join(tmpdir, "in1")
    os.makedirs(indir)
    old_inpath = concoredocker.inpath
    concoredocker.inpath = os.path.join(tmpdir, "in")
    concoredocker.delay = 0.001
    
    with open(os.path.join(indir, "data"), 'w') as f:
        f.write("[7.0, 100, 200]")
    
    concoredocker.s = ''
    concoredocker.simtime = 0
    result = concoredocker.read(1, "data", "[0, 0, 0]")
    
    assert result == [100, 200]
    assert concoredocker.simtime == 7.0
    concoredocker.inpath = old_inpath
    concoredocker.delay = 1

def test_read_missing():
    tmpdir = tempfile.mkdtemp()
    indir = os.path.join(tmpdir, "in1")
    os.makedirs(indir)
    old_inpath = concoredocker.inpath
    concoredocker.inpath = os.path.join(tmpdir, "in")
    concoredocker.delay = 0.001
    
    concoredocker.s = ''
    concoredocker.simtime = 0
    result = concoredocker.read(1, "nofile", "[0, 5, 5]")
    assert result == [5, 5]
    concoredocker.inpath = old_inpath
    concoredocker.delay = 1
