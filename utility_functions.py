import packets
from server import StarryPyServerProtocol

def give_item_to_player(player_protocol, item, count=1):
    item_count = int(count)
    maximum = 1000
    total = item_count
    while item_count > 0:
        x = item_count
        if x > maximum:
            x = maximum
        item_packet = StarryPyServerProtocol.build_packet(packets.Packets.GIVE_ITEM,
                                              packets.give_item_write(item, x+1))
        player_protocol.transport.write(item_packet)
        item_count -= x