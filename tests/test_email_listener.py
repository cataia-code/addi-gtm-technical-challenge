import unittest

from live_demo.email_listener import _is_target_reply


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


if __name__ == "__main__":
    unittest.main()
