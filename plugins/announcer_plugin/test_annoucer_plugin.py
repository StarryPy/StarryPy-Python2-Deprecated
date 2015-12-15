from unittest import TestCase

from mock import Mock

from plugins.announcer_plugin.announcer_plugin import Announcer


class AnnoucerTestCase(TestCase):
    def test_after_connect_success(self):
        mock_factory = Mock()
        mock_config = Mock(colors='colors config')
        mock_protocol = Mock()
        mock_protocol.player.colored_name.return_value = 'player name'
        plugin = Announcer()
        plugin.factory = mock_factory
        plugin.config = mock_config
        plugin.protocol = mock_protocol

        plugin.after_connect_success(None)
        mock_factory.broadcast.assert_called_with(
            'player name logged in.', 'Announcer'
        )
        mock_protocol.player.colored_name.assert_called_with('colors config')

    def test_on_client_disconnect_request(self):
        mock_factory = Mock()
        mock_config = Mock(colors='colors config')
        mock_protocol = Mock()
        mock_protocol.player.colored_name.return_value = 'player name'
        plugin = Announcer()
        plugin.factory = mock_factory
        plugin.config = mock_config
        plugin.protocol = mock_protocol

        plugin.on_client_disconnect_request(None)
        mock_factory.broadcast.assert_called_with(
            'player name logged out.', 'Announcer'
        )
        mock_protocol.player.colored_name.assert_called_with('colors config')

    def test_on_client_disconnect_request_player_is_none(self):
        mock_factory = Mock()
        mock_protocol = Mock()
        mock_protocol.player = None
        plugin = Announcer()
        plugin.factory = mock_factory
        plugin.protocol = mock_protocol

        self.assertFalse(mock_factory.broadcast.called)
