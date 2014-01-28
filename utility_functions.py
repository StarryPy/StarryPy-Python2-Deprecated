from construct import Container
import packets

def give_item_to_player(player_protocol, item, count=1):
    item_count = int(count)
    maximum = 1000
    total = item_count
    while item_count > 0:
        x = item_count
        if x > maximum:
            x = maximum
        item_packet = build_packet(packets.Packets.GIVE_ITEM, packets.give_item_write(item, x+1))
        player_protocol.transport.write(item_packet)
        item_count -= x

def build_packet(packet_type, data):
    """
    Convenience method to build packets for sending.
    :param packet_type: An integer 1 <= packet_type <= 48
    :param data: Data to send.
    :return: The build packet.
    :rtype : str
    """
    length = len(data)
    return packets.packet().build(
        Container(id=packet_type, payload_size=length, data=data))