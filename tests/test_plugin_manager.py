from unittest import TestCase

from mock import Mock, patch, call

from plugin_manager import PluginManager, route


class PluginManagetTestCase(TestCase):
    @patch.object(PluginManager, 'load_plugins')
    @patch('plugin_manager.sys')
    @patch('plugin_manager.path')
    @patch('plugin_manager.ConfigurationManager')
    def test_prepare(
        self, mock_config, mock_path, mock_sys, mock_load_plugins
    ):
        mock_factory = Mock()

        mock_path.child.return_value = Mock(path='test child')
        mock_config.return_value = Mock(
            plugin_path='test path',
            config={
                'initial_plugins': 'test initial plugins'
            }
        )

        pm = PluginManager(mock_factory)
        pm.prepare()

        mock_path.child.assert_called_with('test path')
        mock_sys.path.append.assert_called_with('test child')
        self.assertEqual(mock_load_plugins.call_count, 2)
        mock_load_plugins.assert_has_calls(
            [
                call(
                    [
                        'core.admin_commands_plugin',
                        'core.colored_names',
                        'core.command_plugin',
                        'core.player_manager_plugin',
                        'core.starbound_config_manager'
                    ]
                ),
                call('test initial plugins')
            ]
        )

    def test_get_plugin_name_from_file(self):
        mock_f = Mock()
        mock_f.isdir.return_value = True
        mock_f.basename.return_value = 'test base'

        result = PluginManager.get_plugin_name_from_file(mock_f)
        self.assertEqual(result, 'test base')
        self.assertTrue(mock_f.isdir.called)
        self.assertTrue(mock_f.basename.called)

        mock_f = Mock()
        mock_f.isdir.return_value = False
        result = PluginManager.get_plugin_name_from_file(mock_f)

        self.assertIsNone(result)
        self.assertTrue(mock_f.isdir.called)
        self.assertFalse(mock_f.basename.called)

    @patch.object(PluginManager, 'de_map_plugin_packets')
    @patch('plugin_manager.reversed')
    @patch('plugin_manager.sys')
    @patch('plugin_manager.path')
    @patch('plugin_manager.ConfigurationManager')
    def test_deactivate_plugins(
        self,
        mock_config,
        mock_path,
        mock_sys,
        mock_reversed,
        mock_de_map
    ):
        mock_reversed.side_effect = reversed
        pm = PluginManager(Mock())
        pm.load_order = [1]

        pm.plugins = {
            1: Mock(name='1'),
        }
        pm.deactivate_plugins()

        mock_reversed.assert_called_with([1])
        self.assertTrue(pm.plugins[1].deactivate.called)
        mock_de_map.assert_called_with(pm.plugins[1])

    @patch('plugin_manager.sys')
    @patch('plugin_manager.path')
    @patch('plugin_manager.ConfigurationManager')
    def test_installed_plugins(self, mock_config, mock_path, mock_sys):
        mock_child = Mock(path='test child')
        mock_child.globChildren.return_value = [
            Mock(basename=lambda: 'plugin'),
            Mock(basename=lambda: None),
            Mock(basename=lambda: 'core')
        ]
        mock_path.child.return_value = mock_child

        pm = PluginManager(Mock())
        result = pm.installed_plugins()

        self.assertListEqual(result, ['plugin'])

    @patch('plugin_manager.sys')
    @patch('plugin_manager.path')
    @patch('plugin_manager.ConfigurationManager')
    def test_de_map_plugin_packets(self, mock_config, mock_path, mock_sys):
        mock_plugin = Mock()
        mock_plugin.name = 'Test'

        pm = PluginManager(Mock())
        pm.packets = {
            1: {
                'on': {
                    'Test': 'remove me'
                },
                'after': {'Test2': 'test'}
            },
            2: {
                'on': {
                    'Test': 'remove me',
                    'Test3': 'test'
                },
                'after': {
                    'Test': 'remove me'
                },
            }
        }
        pm.de_map_plugin_packets(mock_plugin)
        self.assertDictEqual(
            pm.packets,
            {
                1: {
                    'on': {},
                    'after': {'Test2': 'test'}
                },
                2: {
                    'on': {
                        'Test3': 'test'
                    },
                    'after': {},
                }
            }
        )

    @patch('plugin_manager.sys')
    @patch('plugin_manager.path')
    @patch('plugin_manager.ConfigurationManager')
    def test_map_plugin_packets(self, mock_config, mock_path, mock_sys):
        mock_plugin = Mock()
        mock_plugin.name = 'Test'
        mock_plugin.overridden_packets = {
            1: {
                'on': 'add me on 1',
                'after': 'add me after 1'
            }
        }
        mock_plugin2 = Mock()
        mock_plugin2.name = 'Test2'
        mock_plugin2.overridden_packets = {
            2: {
                'on': 'add me on 2'
            },
            3: {
                'after': 'add me after 2'
            }
        }

        pm = PluginManager(Mock())
        pm.map_plugin_packets(mock_plugin)

        self.assertDictEqual(
            pm.packets,
            {
                1: {
                    'on': {'Test': (mock_plugin, 'add me on 1')},
                    'after': {'Test': (mock_plugin, 'add me after 1')}
                }
            }
        )

        pm.map_plugin_packets(mock_plugin2)
        self.assertDictEqual(
            pm.packets,
            {
                1: {
                    'on': {'Test': (mock_plugin, 'add me on 1')},
                    'after': {'Test': (mock_plugin, 'add me after 1')}
                },
                2: {
                    'on': {'Test2': (mock_plugin2, 'add me on 2')}
                },
                3: {
                    'after': {'Test2': (mock_plugin2, 'add me after 2')}
                }
            }
        )


class RouteTestCase(TestCase):
    @patch('plugin_manager.reactor')
    @patch('plugin_manager.deferLater')
    @patch('plugin_manager.logging')
    def test_route_response_true(self, mock_logging, mock_defer, mock_reactor):
        test_func = Mock()
        mock_pm = Mock()
        mock_self = Mock()
        mock_self.plugin_manager = mock_pm
        add_err_back = Mock()
        mock_defer.return_value = add_err_back
        logger = Mock()
        mock_logging.getLogger.return_value = logger

        test_f = route(test_func)
        test_f(mock_self, 'data')

        mock_pm.do.assert_called_with(mock_self, 'on', 'data')
        mock_defer.assert_called_with(
            mock_reactor, .01, mock_pm.do, mock_self, 'after', 'data'
        )
        self.assertTrue(add_err_back.addErrback.called)
        self.assertTrue(mock_logging.getLogger.called)

        error_callback = add_err_back.addErrback.call_args[0][0]
        self.assertFalse(logger.error.called)
        error_callback('test')
        self.assertTrue(logger.error.called)

    @patch('plugin_manager.reactor')
    @patch('plugin_manager.deferLater')
    @patch('plugin_manager.logging')
    def test_route_response_false(
        self, mock_logging, mock_defer, mock_reactor
    ):
        test_func = Mock()
        mock_pm = Mock()
        mock_pm.do.return_value = False
        mock_self = Mock()
        mock_self.plugin_manager = mock_pm

        test_f = route(test_func)
        test_f(mock_self, 'data')

        mock_pm.do.assert_called_with(mock_self, 'on', 'data')
        self.assertFalse(mock_defer.called)

    @patch.object(PluginManager, 'deactivate_plugins')
    def test_die(self, mock_deactivate):
        plugin_manager = PluginManager(Mock())

        plugin_manager.die()
        self.assertTrue(mock_deactivate.called)
