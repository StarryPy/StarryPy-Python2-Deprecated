from unittest import TestCase

from mock import Mock, patch

from plugins.chat_logger.chat_logger import ChatLogger


class ChatLoggerTestCase(TestCase):

    @patch('plugins.chat_logger.chat_logger.chat_sent')
    def test_on_chat_sent(self, mock_chat_sent):
        mock_data = Mock(data='data data')
        mock_parsed = Mock()
        mock_parsed.parse.return_value = Mock(message='test message')
        mock_chat_sent.return_value = mock_parsed
        mock_logger = Mock()
        mock_protocol = Mock()
        mock_protocol.player.name = 'player name'
        plugin = ChatLogger()
        plugin.protocol = mock_protocol
        plugin.logger = mock_logger

        plugin.on_chat_sent(mock_data)
        mock_parsed.parse.assert_called_with('data data')
        mock_logger.info.assert_called_with(
            'Chat message sent: <%s> %s', 'player name', 'test message'
        )
