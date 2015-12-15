from unittest import TestCase
from datetime import datetime

from mock import Mock, patch

from plugins.admin_messenger.admin_messenger import AdminMessenger
from plugins.core.player_manager_plugin import UserLevels


class AdminMessengerTestCase(TestCase):
    def test_activate(self):
        plugin = AdminMessenger()
        plugin.config = Mock(chat_prefix='test prefix')

        with self.assertRaises(AttributeError):
            self.plugin.prefix

        plugin.activate()
        self.assertEqual(plugin.prefix, 'test prefix')

    @patch.object(AdminMessenger, 'message_admins')
    @patch.object(AdminMessenger, 'broadcast_message')
    @patch('plugins.admin_messenger.admin_messenger.packets')
    def test_on_chat_sent_broadcast(
        self, mock_packets, mock_broadcast, mock_admins
    ):
        mock_parse = Mock()
        message = Mock(message='###broadcast message')
        mock_parse.parse.return_value = message
        mock_packets.chat_sent.return_value = mock_parse
        mock_data = Mock(data='test data')
        plugin = AdminMessenger()
        plugin.config = Mock()
        plugin.activate()
        plugin.prefix = '#'

        self.assertFalse(plugin.on_chat_sent(mock_data))
        mock_parse.parse.assert_called_with('test data')
        mock_broadcast.assert_called_with(message)

    @patch.object(AdminMessenger, 'message_admins')
    @patch.object(AdminMessenger, 'broadcast_message')
    @patch('plugins.admin_messenger.admin_messenger.packets')
    def test_on_chat_sent_message_admins(
        self, mock_packets, mock_broadcast, mock_admins
    ):
        plugin = AdminMessenger()
        plugin.config = Mock()
        plugin.activate()
        plugin.prefix = '#'
        mock_parse = Mock()
        mock_data = Mock(data='test data')
        message = Mock(message='##admin message')
        mock_parse.parse.return_value = message
        mock_packets.chat_sent.return_value = mock_parse

        self.assertFalse(plugin.on_chat_sent(mock_data))
        mock_admins.assert_called_with(message)

    @patch.object(AdminMessenger, 'message_admins')
    @patch.object(AdminMessenger, 'broadcast_message')
    @patch('plugins.admin_messenger.admin_messenger.packets')
    def test_on_chat_sent_normal_message(
        self, mock_packets, mock_broadcast, mock_admins
    ):
        mock_parse = Mock()
        mock_data = Mock(data='test data')
        plugin = AdminMessenger()
        plugin.config = Mock()
        plugin.activate()
        plugin.prefix = '#'
        message = Mock(message='test message')
        mock_parse.parse.return_value = message

        self.assertTrue(plugin.on_chat_sent(mock_data))
        self.assertFalse(mock_admins.called)
        self.assertFalse(mock_broadcast.called)

    @patch('plugins.admin_messenger.admin_messenger.datetime')
    def test_add_timestamp(self, mock_datetime):
        current_datetime = datetime.now()
        mock_datetime.now.return_value = current_datetime
        plugin = AdminMessenger()
        plugin.config = Mock()

        result = plugin.add_timestamp()
        self.assertEqual(
            result,
            '^red;<{}> '.format(current_datetime.strftime('%H:%M'))
        )

        result = plugin.add_timestamp(True)
        self.assertEqual(
            result,
            '^red;<{}> ^yellow;'.format(current_datetime.strftime('%H:%M'))
        )

        plugin.config.chattimestamps = False
        result = plugin.add_timestamp()
        self.assertEqual(result, '')

    @patch.object(AdminMessenger, 'add_timestamp')
    def test_message_admins(self, mock_add_timestamp):
        mock_logger = Mock()
        mock_config = Mock()
        mock_config.colors = {'moderator': 'moderator colors'}
        mock_message = Mock()
        mock_message.message = '##test'
        mock_add_timestamp.return_value = 'with add_normalizer'
        mock_just_player = Mock()
        mock_just_player.player.access_level = UserLevels.GUEST
        mock_player_moderator = Mock()
        mock_player_moderator.player.access_level = UserLevels.MODERATOR
        mock_factory = Mock()
        mock_factory.protocols = {
            'normal player': mock_just_player,
            'moderator': mock_player_moderator
        }
        mock_protocol = Mock()
        mock_protocol.player.colored_name.return_value = 'player colors'
        plugin = AdminMessenger()
        plugin.factory = mock_factory
        plugin.config = mock_config
        plugin.logger = mock_logger
        plugin.protocol = mock_protocol

        plugin.message_admins(mock_message)
        mock_player_moderator.send_chat_message.assert_called_with(
            '{}{}ADMIN: ^yellow;<{}^yellow;> {}{}'.format(
                'with add_normalizer',
                'moderator colors',
                'player colors',
                'moderator colors',
                'test'
            )
        )
        mock_logger.info.assert_called_with(
            'Received an admin message from %s. Message: %s',
            mock_protocol.player.name, 'test'
        )
        self.assertFalse(mock_just_player.send_chat_message.called)
        mock_add_timestamp.assert_called_with(add_normalizer=True)

    @patch.object(AdminMessenger, 'add_timestamp')
    def test_broadcast_message(self, mock_add_timestamp):
        mock_logger = Mock()
        mock_config = Mock()
        mock_config.colors = {
            'admin': 'admin colors',
            'default': 'default colors'
        }
        mock_message = Mock()
        mock_message.message = '###test'
        mock_add_timestamp.return_value = 'without add_normalizer'
        mock_just_player = Mock()
        mock_player_moderator = Mock()
        mock_factory = Mock()
        mock_factory.protocols = {
            'normal player': mock_just_player,
            'moderator': mock_player_moderator
        }
        mock_protocol = Mock()
        mock_protocol.player.access_level = UserLevels.ADMIN
        plugin = AdminMessenger()
        plugin.factory = mock_factory
        plugin.config = mock_config
        plugin.logger = mock_logger
        plugin.protocol = mock_protocol
        expected_message = '{}{}BROADCAST: ^red;{}{}'.format(
            'without add_normalizer', 'admin colors', 'TEST',
            'default colors'
        )

        plugin.broadcast_message(mock_message)
        mock_player_moderator.send_chat_message.assert_called_with(
            expected_message
        )
        mock_just_player.send_chat_message.assert_called_with(expected_message)
        mock_logger.info.assert_called_with(
            'Broadcast from %s. Message: %s',
            mock_protocol.player.name, 'TEST'
        )
        self.assertFalse(mock_protocol.send_chat_message.called)

    def test_broadcast_message_not_admin(self):
        mock_protocol = Mock()
        mock_protocol.player.access_level = UserLevels.GUEST
        plugin = AdminMessenger()
        plugin.protocol = mock_protocol

        result = plugin.broadcast_message('test')
        self.assertFalse(result)
        mock_protocol.send_chat_message.assert_called_with(
            'You are not authorized to do this.'
        )
