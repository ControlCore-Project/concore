# pm_jl.jl -- Julia plant model for the concore demo

include("concore.jl")
using .Concore

pm(u) = u .+ 0.01

Concore.default_maxtime!(150)
Concore.delay = 0.02

init_simtime_u = "[0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0]"

ym = initval(init_simtime_ym)

while Concore.simtime < Concore.maxtime
    u = initval(init_simtime_u)
    while unchanged()
        u = concore_read(1, "u", init_simtime_u)
    end

    ym = pm(u)
    println("$(Concore.simtime). u=$(u) ym=$(ym)")
    concore_write(1, "ym", ym; delta=1)
end

println("retry=$(Concore.retrycount)")
