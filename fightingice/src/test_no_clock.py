"""Integration test for native no-clock state and capped compatibility."""
import unittest
from bridge import bridge

class NoClock(unittest.TestCase):
    def test_crosses_previous_limit_without_reset(self):
        with bridge() as e:
            s=e.start(0,400)
            self.assertIsNone(s['framesLeft'])
            for _ in range(7):
                s=e.step(600,'NEUTRAL','NEUTRAL')
            self.assertEqual(s['frame'],4200)
            self.assertFalse(s['terminated'])
            self.assertEqual([s[k]['hp'] for k in ('p1','p2')],[400,400])
    def test_timed_exhibitions_keep_their_cap(self):
        with bridge() as e:
            e.start(60,400)
            s=e.step(120,'NEUTRAL','NEUTRAL')
            self.assertEqual((s['frame'],s['by']),(60,'time'))
if __name__=='__main__':unittest.main()
