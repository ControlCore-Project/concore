using Documenter

include(joinpath(@__DIR__, "..", "concore.jl"))
using .Concore

makedocs(;
    modules=[Concore],
    sitename="Concore.jl",
    checkdocs=:exports,
    format=Documenter.HTML(; inventory_version="dev"),
    pages=[
        "Home" => "index.md",
        "Getting Started" => "getting-started.md",
        "API Reference" => "api.md",
        "Backends" => "backends.md",
        "Wire Format" => "wire-format.md",
    ],
)
