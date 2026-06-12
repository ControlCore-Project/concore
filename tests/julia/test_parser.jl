@testset "safe_parse_list" begin

    # Standard numeric formats
    @testset "standard float list" begin
        @test Concore.safe_parse_list("[1.0, 2.0, 3.0]") == [1.0, 2.0, 3.0]
    end

    @testset "single element" begin
        @test Concore.safe_parse_list("[42.0]") == [42.0]
    end

    @testset "two elements" begin
        @test Concore.safe_parse_list("[1.5, 2.5]") == [1.5, 2.5]
    end

    @testset "many elements (10)" begin
        result = Concore.safe_parse_list("[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]")
        @test result == collect(0.0:9.0)
        @test length(result) == 10
    end

    @testset "integer-only list" begin
        @test Concore.safe_parse_list("[1, 2, 3]") == [1.0, 2.0, 3.0]
    end

    @testset "mixed int and float" begin
        @test Concore.safe_parse_list("[1, 2.5, 3]") == [1.0, 2.5, 3.0]
    end

    @testset "zero values" begin
        @test Concore.safe_parse_list("[0.0]") == [0.0]
        @test Concore.safe_parse_list("[0]") == [0.0]
        @test Concore.safe_parse_list("[0.0, 0.0, 0.0]") == [0.0, 0.0, 0.0]
    end

    # Negative numbers
    @testset "negative float" begin
        @test Concore.safe_parse_list("[-1.5]") == [-1.5]
    end

    @testset "negative integers" begin
        @test Concore.safe_parse_list("[-1, -2, -3]") == [-1.0, -2.0, -3.0]
    end

    @testset "mixed positive and negative" begin
        @test Concore.safe_parse_list("[-1.5, 0.0, 2.5]") == [-1.5, 0.0, 2.5]
    end

    @testset "very small negative" begin
        @test Concore.safe_parse_list("[-0.001]") ≈ [-0.001]
    end

    # Scientific notation / extreme values
    @testset "scientific notation" begin
        @test Concore.safe_parse_list("[1e-15, 1e15]") ≈ [1e-15, 1e15]
    end

    @testset "small scientific notation" begin
        @test Concore.safe_parse_list("[1.5e-10]") ≈ [1.5e-10]
    end

    @testset "large scientific notation" begin
        @test Concore.safe_parse_list("[3.14e8]") ≈ [3.14e8]
    end

    @testset "negative scientific notation" begin
        @test Concore.safe_parse_list("[-1.23e-4]") ≈ [-1.23e-4]
    end

    @testset "very large number" begin
        @test Concore.safe_parse_list("[1e300]") ≈ [1e300]
    end

    @testset "very small number" begin
        @test Concore.safe_parse_list("[1e-300]") ≈ [1e-300]
    end

    # NumPy wrapper handling
    @testset "np.float64 wrapper" begin
        @test Concore.safe_parse_list("[np.float64(1.5)]") == [1.5]
    end

    @testset "np.float32 wrapper" begin
        @test Concore.safe_parse_list("[np.float32(2.0)]") == [2.0]
    end

    @testset "numpy.int32 wrapper" begin
        @test Concore.safe_parse_list("[numpy.int32(42)]") == [42.0]
    end

    @testset "np.int64 wrapper" begin
        @test Concore.safe_parse_list("[np.int64(7)]") == [7.0]
    end

    @testset "multiple numpy wrappers" begin
        @test Concore.safe_parse_list("[np.float64(1.0), np.float64(2.0)]") == [1.0, 2.0]
    end

    @testset "numpy wrapper with negative" begin
        @test Concore.safe_parse_list("[np.float64(-3.14)]") ≈ [-3.14]
    end

    @testset "numpy wrapper with zero" begin
        @test Concore.safe_parse_list("[np.float64(0.0)]") == [0.0]
    end

    @testset "mixed numpy and plain" begin
        @test Concore.safe_parse_list("[np.float64(1.5), 2.0, np.int32(3)]") == [1.5, 2.0, 3.0]
    end

    # Python boolean and None handling
    @testset "Python True" begin
        @test Concore.safe_parse_list("[True]") == [1.0]
    end

    @testset "Python False" begin
        @test Concore.safe_parse_list("[False]") == [0.0]
    end

    @testset "Python None" begin
        @test Concore.safe_parse_list("[None]") == [0.0]
    end

    @testset "multiple Python booleans" begin
        @test Concore.safe_parse_list("[True, False, True]") == [1.0, 0.0, 1.0]
    end

    @testset "mixed booleans and numbers" begin
        @test Concore.safe_parse_list("[True, 2.5, False]") == [1.0, 2.5, 0.0]
    end

    @testset "True False None together" begin
        @test Concore.safe_parse_list("[True, False, None]") == [1.0, 0.0, 0.0]
    end

    @testset "mixed numpy, booleans, and numbers" begin
        @test Concore.safe_parse_list("[np.float64(1.5), True, 2.0, False]") == [1.5, 1.0, 2.0, 0.0]
    end

    # Whitespace handling
    @testset "leading whitespace" begin
        @test Concore.safe_parse_list("  [1.0, 2.0]") == [1.0, 2.0]
    end

    @testset "trailing whitespace" begin
        @test Concore.safe_parse_list("[1.0, 2.0]   ") == [1.0, 2.0]
    end

    @testset "leading and trailing whitespace" begin
        @test Concore.safe_parse_list("  [1.0, 2.0]  ") == [1.0, 2.0]
    end

    @testset "extra spaces around commas" begin
        @test Concore.safe_parse_list("[1.0 ,  2.0 , 3.0]") == [1.0, 2.0, 3.0]
    end

    @testset "spaces inside brackets" begin
        @test Concore.safe_parse_list("[ 1.0, 2.0 ]") == [1.0, 2.0]
    end

    @testset "tab characters" begin
        @test Concore.safe_parse_list("[\t1.0,\t2.0\t]") == [1.0, 2.0]
    end

    @testset "newline in whitespace" begin
        @test Concore.safe_parse_list("\n[1.0, 2.0]\n") == [1.0, 2.0]
    end

    # Return types
    @testset "always returns Vector{Float64}" begin
        result = Concore.safe_parse_list("[1, 2, 3]")
        @test result isa Vector{Float64}
    end

    @testset "integer input returns Float64" begin
        result = Concore.safe_parse_list("[42]")
        @test eltype(result) == Float64
    end

    @testset "single element returns Vector" begin
        result = Concore.safe_parse_list("[1.0]")
        @test result isa Vector{Float64}
        @test length(result) == 1
    end

    # Error cases
    @testset "empty string throws" begin
        @test_throws Exception Concore.safe_parse_list("")
    end

    @testset "no brackets throws" begin
        @test_throws Exception Concore.safe_parse_list("1.0, 2.0")
    end

    @testset "missing closing bracket throws" begin
        @test_throws Exception Concore.safe_parse_list("[1.0, 2.0")
    end

    @testset "missing opening bracket throws" begin
        @test_throws Exception Concore.safe_parse_list("1.0, 2.0]")
    end

    @testset "empty brackets throws" begin
        @test_throws Exception Concore.safe_parse_list("[]")
    end

    @testset "non-numeric content throws" begin
        @test_throws Exception Concore.safe_parse_list("[hello, world]")
    end

    @testset "only whitespace throws" begin
        @test_throws Exception Concore.safe_parse_list("   ")
    end

    @testset "random text in list throws" begin
        @test_throws Exception Concore.safe_parse_list("[1.0, abc, 3.0]")
    end

    # Precision and edge cases
    @testset "high precision value" begin
        @test Concore.safe_parse_list("[3.141592653589793]") ≈ [π] atol=1e-15
    end

    @testset "many decimal places" begin
        @test Concore.safe_parse_list("[1.123456789012345]") ≈ [1.123456789012345]
    end

    @testset "positive zero" begin
        @test Concore.safe_parse_list("[0.0]") == [0.0]
    end

    @testset "negative zero" begin
        result = Concore.safe_parse_list("[-0.0]")
        @test result[1] == 0.0  # -0.0 == 0.0 in IEEE 754
    end

    @testset "Inf value" begin
        @test Concore.safe_parse_list("[Inf]") == [Inf]
    end

    @testset "negative Inf" begin
        @test Concore.safe_parse_list("[-Inf]") == [-Inf]
    end

    @testset "twenty elements" begin
        vals = join(["$i.0" for i in 1:20], ", ")
        result = Concore.safe_parse_list("[$vals]")
        @test length(result) == 20
        @test result == collect(1.0:20.0)
    end

    @testset "repeated values" begin
        @test Concore.safe_parse_list("[1.0, 1.0, 1.0]") == [1.0, 1.0, 1.0]
    end

    @testset "alternating signs" begin
        @test Concore.safe_parse_list("[1.0, -1.0, 1.0, -1.0]") == [1.0, -1.0, 1.0, -1.0]
    end

    # Realistic wire format strings
    @testset "typical concore wire string (simtime + data)" begin
        result = Concore.safe_parse_list("[5.0, 42.0, 3.14]")
        @test result == [5.0, 42.0, 3.14]
    end

    @testset "simtime=0 initial string" begin
        result = Concore.safe_parse_list("[0.0, 0.0]")
        @test result == [0.0, 0.0]
    end

    @testset "large simtime" begin
        result = Concore.safe_parse_list("[999.0, 1.0, 2.0, 3.0]")
        @test result[1] == 999.0
    end

    @testset "Python str output format" begin
        @test Concore.safe_parse_list("[1.0, 2.0, 3.0]") == [1.0, 2.0, 3.0]
    end

    @testset "Python str with integers" begin
        @test Concore.safe_parse_list("[0, 1, 2]") == [0.0, 1.0, 2.0]
    end

    @testset "numpy array str format" begin
        @test Concore.safe_parse_list("[np.float64(1.5), np.float64(2.5)]") == [1.5, 2.5]
    end

end
