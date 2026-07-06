import unittest

from gale.net.peer import Peer


class PeerRttTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.peer = Peer(peer_id=1, address=("127.0.0.1", 9000), token=42)

    def test_first_sample_sets_rtt_directly(self) -> None:
        self.peer.update_rtt(0.1)
        self.assertAlmostEqual(self.peer.rtt, 0.1)

    def test_later_samples_are_smoothed(self) -> None:
        self.peer.update_rtt(0.1)
        self.peer.update_rtt(0.5)
        expected = 0.875 * 0.1 + 0.125 * 0.5
        self.assertAlmostEqual(self.peer.rtt, expected)


if __name__ == "__main__":
    unittest.main()
