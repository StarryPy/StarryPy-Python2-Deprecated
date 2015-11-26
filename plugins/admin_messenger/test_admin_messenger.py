from unittest import TestCase

from mock import Mock, patch

from plugins.admin_messenger.admin_messenger import AdminMessenger


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
