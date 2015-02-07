import logging
from construct import Construct, Struct, Byte, BFloat64, Flag, \
    String, Container, Field
from construct.core import _read_stream, _write_stream, Adapter


class SignedVLQ(Construct):
    logger = logging.getLogger('starrypy.packets.SignedVLQ')

    def _parse(self, stream, context):
        value = 0
        while True:
            tmp = ord(_read_stream(stream, 1))
            value = (value << 7) | (tmp & 0x7f)
            if tmp & 0x80 == 0:
                break
        if (value & 1) == 0x00:
            return value >> 1
        else:
            return -((value >> 1) + 1)

    def _build(self, obj, stream, context):
        try:
            value = abs(obj * 2)
            if obj < 0:
                value -= 1
            VLQ("")._build(value, stream, context)
        except:
            self.logger.exception("Error building SignedVLQ.")
            raise


class VLQ(Construct):
    logger = logging.getLogger('starrypy.packets.SignedVLQ')

    def _parse(self, stream, context):
        value = 0
        while True:
            tmp = ord(_read_stream(stream, 1))
            value = (value << 7) | (tmp & 0x7f)
            if tmp & 0x80 == 0:
                break
        return value

    def _build(self, obj, stream, context):
        result = bytearray()
        value = int(obj)
        if obj == 0:
            _write_stream(stream, 1, chr(0))
            return
        while value > 0:
            byte = value & 0x7f
            value >>= 7
            if value != 0:
                byte |= 0x80
            result.insert(0, byte)
        if len(result) > 1:
            result[0] |= 0x80
            result[-1] ^= 0x80
        _write_stream(stream, len(result), "".join([chr(x) for x in result]))


star_string = lambda name="star_string": StarStringAdapter(star_string_struct(name))


class StarStringAdapter(Adapter):
    def _encode(self, obj, context):
        return Container(length=len(obj), string=obj)

    def _decode(self, obj, context):
        return obj.string

class Joiner(Adapter):
    def _encode(self, obj, context):
        return obj
    def _decode(self, obj, context):
        return "".join(obj)

star_string_struct = lambda name="star_string": Struct(name,
                                                       VLQ("length"),
                                                       String("string", lambda ctx: ctx.length))

class VariantVariant(Construct):
    def _parse(self, stream, context):
        l = VLQ("").parse_stream(stream)
        return [Variant("").parse_stream(stream) for _ in range(l)]

class DictVariant(Construct):
    def _parse(self, stream, context):
        l = VLQ("").parse_stream(stream)
        c = {}
        for x in range(l):
            key = star_string("").parse_stream(stream)
            value = Variant("").parse_stream(stream)
            c[key] = value
        return c

class WarpVariant(Construct):
# Not all variants have been properly treated!
    def _parse(self, stream, context):
        x = Byte("").parse_stream(stream)
        if x == 0:
            return None
        elif x == 1:
            return star_string().parse_stream(stream)
        elif x == 2:
            return None
        elif x == 3:
            flag = Flag("").parse_stream(stream)
            return Field("", 16).parse_stream(stream).encode("hex")
    def _build(self, obj, stream, context):
        if len(obj) == 32:
            _write_stream(stream, 1, chr(3))
            _write_stream(stream, 1, chr(1))
            _write_stream(stream, len(obj.decode("hex")), obj.decode("hex"))
            return
        elif obj is "outpost":
            _write_stream(stream, 1, chr(1))
            star_string()._build(obj, stream, context)
            return
        elif obj is None:
            _write_stream(stream, 1, chr(4))
            _write_stream(stream, 1, chr(0))
            return

class Variant(Construct):
    def _parse(self, stream, context):
        x = Byte("").parse_stream(stream)
        if x == 1:
            return None
        elif x == 2:
            return BFloat64("").parse_stream(stream)
        elif x == 3:
            return Flag("").parse_stream(stream)
        elif x == 4:
            return SignedVLQ("").parse_stream(stream)
        elif x == 5:
            return star_string().parse_stream(stream)
        elif x == 6:
            return VariantVariant("").parse_stream(stream)
        elif x == 7:
            return DictVariant("").parse_stream(stream)

class StarByteArray(Construct):
    def _parse(self, stream, context):
        l = VLQ("").parse_stream(stream)
        return _read_stream(stream, l)
    def _build(self, obj, stream, context):
        _write_stream(stream, len(obj), VLQ("").build(len(obj))+obj)

