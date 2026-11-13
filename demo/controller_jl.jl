# controller_jl.jl -- Julia bang-bang controller for the concore demo

include("concore.jl")
using .Concore

const ysp = 3.0

function controller(ym)
    if ym[1] < ysp
        return 1.01 .* ym
    end
    return 0.9 .* ym
end

Concore.default_maxtime!(150)
Concore.delay = 0.02

init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"

u = initval(init_simtime_u)

while Concore.simtime < Concore.maxtime
    ym = initval(init_simtime_ym)
    while unchanged()
        ym = concore_read(1, "ym", init_simtime_ym)
    end

    u = controller(ym)
    println("$(Concore.simtime). u=$(u) ym=$(ym)")
    concore_write(1, "u", u; delta=0)
end

println("retry=$(Concore.retrycount)")
