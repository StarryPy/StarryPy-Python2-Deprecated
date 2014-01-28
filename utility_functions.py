import logging

from construct import Container

import packets


logger = logging.getLogger("starrypy.utility_functions")


def give_item_to_player(player_protocol, item, count=1):
    logger.debug("Giving item %s (count: %d) to %s", item, count, player_protocol.player.name)
    item_count = int(count)
    maximum = 1000
    total = item_count
    while item_count > 0:
        x = item_count
        if x > maximum:
            x = maximum
        item_packet = build_packet(packets.Packets.GIVE_ITEM, packets.give_item_write(item, x + 1))
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


class Planet(object):
    def __init__(self, sector, x, y, z, planet, satellite):
        self.sector = sector
        self.x = x
        self.y = y
        self.z = z
        self.planet = planet
        self.satellite = satellite

    def __str__(self):
        return "%s:%d:%d:%d:%d:%d" % (self.sector, self.x, self.y, self.z, self.planet, self.satellite)


def move_ship_to_coords(protocol, sector, x, y, z, planet, satellite):
    logger.info("Moving %s's ship to coordinates: %s", protocol.player.name,
                ":".join((sector, x, y, z, planet, satellite)))
    x, y, z, planet, satellite = map(int, (x, y, z, planet, satellite))
    warp_packet = build_packet(packets.Packets.WARP_COMMAND,
                               packets.warp_command_write(t="MOVE_SHIP", sector=sector, x=x, y=y, z=z,
                                                          planet=planet,
                                                          satellite=satellite, player="".encode('utf-8')))
    protocol.client_protocol.transport.write(warp_packet)