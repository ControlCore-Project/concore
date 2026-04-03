import os


# can't import mkconcore directly (sys.argv at module level), so we duplicate the parser
def _load_tool_config(filepath):
    tools = {}
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if v:
                tools[k] = v
    return tools


class TestLoadToolConfig:
    def test_basic_overrides(self, temp_dir):
        cfg = os.path.join(temp_dir, "concore.tools")
        with open(cfg, "w") as f:
            f.write("CPPEXE=/usr/local/bin/g++-12\n")
            f.write("PYTHONEXE=/usr/bin/python3.11\n")

        tools = _load_tool_config(cfg)
        assert tools["CPPEXE"] == "/usr/local/bin/g++-12"
        assert tools["PYTHONEXE"] == "/usr/bin/python3.11"
        assert "VEXE" not in tools

    def test_comments_and_blanks_ignored(self, temp_dir):
        cfg = os.path.join(temp_dir, "concore.tools")
        with open(cfg, "w") as f:
            f.write("# custom tool paths\n")
            f.write("\n")
            f.write("OCTAVEEXE = /snap/bin/octave\n")
            f.write("# MATLABEXE = /opt/matlab/bin/matlab\n")

        tools = _load_tool_config(cfg)
        assert tools["OCTAVEEXE"] == "/snap/bin/octave"
        assert "MATLABEXE" not in tools

    def test_empty_value_skipped(self, temp_dir):
        cfg = os.path.join(temp_dir, "concore.tools")
        with open(cfg, "w") as f:
            f.write("CPPWIN=\n")
            f.write("VEXE = \n")

        tools = _load_tool_config(cfg)
        assert "CPPWIN" not in tools
        assert "VEXE" not in tools

    def test_value_with_equals_sign(self, temp_dir):
        cfg = os.path.join(temp_dir, "concore.tools")
        with open(cfg, "w") as f:
            f.write("CPPEXE=C:\\Program Files\\g++=fast\n")

        tools = _load_tool_config(cfg)
        assert tools["CPPEXE"] == "C:\\Program Files\\g++=fast"

    def test_whitespace_around_key_value(self, temp_dir):
        cfg = os.path.join(temp_dir, "concore.tools")
        with open(cfg, "w") as f:
            f.write("  VWIN  =  C:\\iverilog\\bin\\iverilog.exe  \n")

        tools = _load_tool_config(cfg)
        assert tools["VWIN"] == "C:\\iverilog\\bin\\iverilog.exe"

    def test_empty_file(self, temp_dir):
        cfg = os.path.join(temp_dir, "concore.tools")
        with open(cfg, "w") as _:
            pass

        tools = _load_tool_config(cfg)
        assert tools == {}
