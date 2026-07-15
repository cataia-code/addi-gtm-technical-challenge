import unittest

from unittest.mock import patch

from live_demo.email_listener import _is_target_reply, _looks_like_demo_reply


class EmailListenerTest(unittest.TestCase):
    def test_target_reply_filters_thread_unread_sent_and_age(self):
        message = {
            "threadId": "thread-1",
            "labelIds": ["UNREAD", "INBOX"],
            "internalDate": "2000",
        }

        self.assertTrue(_is_target_reply(message, "thread-1", after_epoch_ms=1000))
        self.assertFalse(_is_target_reply(message, "thread-2", after_epoch_ms=1000))
        self.assertFalse(_is_target_reply({**message, "labelIds": ["INBOX"]}, "thread-1", after_epoch_ms=1000))
        self.assertFalse(_is_target_reply({**message, "labelIds": ["UNREAD", "SENT"]}, "thread-1", after_epoch_ms=1000))
        self.assertFalse(_is_target_reply(message, "thread-1", after_epoch_ms=3000))

    def test_demo_fallback_accepts_button_reply_and_rejects_original_outreach(self):
        reply = {"internalDate": "2000"}
        original = {"internalDate": "2000"}

        with patch("live_demo.email_listener.extract_message_text", return_value="Si me interesa. Contexto: Brand_0145"):
            self.assertTrue(_looks_like_demo_reply(reply, "Brand_0145", after_epoch_ms=1000))

        with patch(
            "live_demo.email_listener.extract_message_text",
            return_value="Notamos que Brand_0145 proceso COP 4908 MM. Tus clientes ya usan financiamiento Addi.",
        ):
            self.assertFalse(_looks_like_demo_reply(original, "Brand_0145", after_epoch_ms=1000))


if __name__ == "__main__":
    unittest.main()
