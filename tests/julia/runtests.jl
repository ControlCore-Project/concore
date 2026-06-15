using Test

include(joinpath(@__DIR__, "..", "..", "concore.jl"))
using .Concore

@testset "Concore.jl" begin
    include("test_parser.jl")
    include("test_config.jl")
    include("test_sync.jl")
    include("test_protocol.jl")
end
