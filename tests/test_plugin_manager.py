from unittest import TestCase

from mock import Mock, patch, call

from plugin_manager import PluginManager


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

    @patch('plugin_manager.reversed')
    @patch('plugin_manager.sys')
    @patch('plugin_manager.path')
    @patch('plugin_manager.ConfigurationManager')
    def test_deactivate_plugins(
        self,
        mock_config,
        mock_path,
        mock_sys,
        mock_reversed
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

    @patch('plugin_manager.__import__')
    @patch('plugin_manager.inspect.getmembers')
    @patch('plugin_manager.sys')
    @patch('plugin_manager.path')
    @patch('plugin_manager.ConfigurationManager')
    def test_import_plugin(
        self,
        mock_config,
        mock_path,
        mock_sys,
        mock_getmembers,
        mock_import
    ):
        mock_factory = Mock()
        mock_import.return_value = ''
