from unittest import TestCase

from base_plugin import BasePlugin


class BasePluginTestCase(TestCase):
    def test_mapping_override_packets_dont_include_base_plugin(self):
        base_plugin = BasePlugin()
        with self.assertRaises(AttributeError):
            base_plugin.overridden_packets

    def test_activation_deactivation(self):
        class TestPlugin(BasePlugin):
            pass

        test_plugin1 = TestPlugin()
        self.assertFalse(test_plugin1.active)
        self.assertTrue(test_plugin1.activate())
        self.assertTrue(test_plugin1.active)

        self.assertTrue(test_plugin1.deactivate())
        self.assertFalse(test_plugin1.active)

    def test_mappig_override_packets(self):
        class TestPlugin(BasePlugin):
            def on_chat_sent(self, data):
                pass

            def on_chat_received(self, data):
                pass

        class TestPlugin2(BasePlugin):
            def on_burn_container(self, data):
                pass

            def after_burn_container(self, data):
                pass

        test_plugin2 = TestPlugin2()
        test_plugin = TestPlugin()
        self.maxDiff = None
        self.assertDictEqual(
            test_plugin.overridden_methods,
            {
                5: {
                    'on': test_plugin.on_chat_received
                },
                14: {
                    'on': test_plugin.on_chat_sent
                }
            }
        )
        self.assertDictEqual(
            test_plugin2.overridden_methods,
            {
                44: {
                    'on': test_plugin2.on_burn_container,
                    'after': test_plugin2.after_burn_container
                }
            }
        )

    def test_unicode_str(self):
        class TestPlugin(BasePlugin):
            version = 1
            pass

        self.assertEqual(
            str(TestPlugin()),
            '<Plugin instance: Base Plugin (version 1)>'
        )

        self.assertEqual(
            unicode(TestPlugin()),
            '<Plugin instance: Base Plugin (version 1)>'
        )

        self.assertNotEqual(
            repr(TestPlugin()),
            '<Plugin instance: Base Plugin (version 1)>'
        )
