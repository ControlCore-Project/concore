import concore
import concore2
import time
from osparc_control import CommandManifest
from osparc_control import CommandParameter
from osparc_control import CommandType
from osparc_control import PairedTransmitter
# declare some commands to which a reply can be provided
CONCORE_MANIFEST = CommandManifest(
    action="fun",
    description="function call",
    params=[
        CommandParameter(name="u", description="control move"),
    ],
    command_type=CommandType.WITH_IMMEDIATE_REPLY,
)


print("funbody 0mq")
# initialization of 0mq/osparc-control "paired_transmitter"
paired_transmitter = PairedTransmitter(
    remote_host="localhost",
    exposed_commands=[CONCORE_MANIFEST],
    remote_port=2346,
    listen_port=2345,)

paired_transmitter.start_background_sync()

concore.delay = 0.07
concore2.delay = 0.07
concore2.inpath = concore.inpath
concore2.outpath = concore.outpath
concore2.simtime = 0
concore.default_maxtime(100)
init_simtime_u = "[0.0, 0.0, 0.0]"
init_simtime_ym = "[0.0, 0.0, 0.0]"

u = concore.initval(init_simtime_u)
ym = concore2.initval(init_simtime_ym)
while(concore2.simtime<concore.maxtime):
    #while concore.unchanged():
    #    u = concore.read(concore.iport['U1'],"u",init_simtime_u)
    command_list = paired_transmitter.get_incoming_requests()
    while len(command_list)==0:
        time.sleep(.01)
        command_list = paired_transmitter.get_incoming_requests()
    if len(command_list)>1:
        print("too many commands at once!")
    command = command_list[0]
    if command.action == CONCORE_MANIFEST.action:
        u = command.params["u"]
        concore.simtime = u[0]
        u = u[1:] 
        concore.write(concore.oport['U2'],"u",u)
        print(u)
        old2 = concore2.simtime
        while concore2.unchanged() or concore2.simtime <= old2:
            ym = concore2.read(concore.iport['Y2'],"ym",init_simtime_ym)
        ym = [concore2.simtime]+ym
        print(f"Replying to {command.action} with {ym}")
        paired_transmitter.reply_to_command(
           request_id=command.request_id, payload=ym)
    else:
        print("undefined action"+str(command.action)) 
        quit()
    #concore2.write(concore.oport['Y1'],"ym",ym)
    print("funbody u="+str(u)+" ym="+str(ym)+" time="+str(concore2.simtime))
paired_transmitter.stop_background_sync()
print("retry="+str(concore.retrycount))
