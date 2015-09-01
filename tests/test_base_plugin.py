from unittest import TestCase

from base_plugin import BasePlugin


class BasePluginTestCase(TestCase):
    def test_mapping_override_packets_dont_include_base_plugin(self):
        base_plugin = BasePlugin()
        with self.assertRaises(AttributeError):
            base_plugin.override_packets

    def test_mappig_override_packets(self):
        class TestPlugin(BasePlugin):
            def on_chat_sent(self, data):
                pass

            def on_chat_received(self, data):
                pass

        class TestPlugin2(BasePlugin):
            def on_burn_container(self, data):
                pass

        test_plugin2 = TestPlugin2()
        test_plugin = TestPlugin()
        self.assertListEqual(test_plugin.override_packets, [5, 14])
        self.assertListEqual(test_plugin2.override_packets, [44])
