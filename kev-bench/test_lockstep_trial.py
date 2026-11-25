import unittest
from lockstep_trial import pair, advance, FORMAT
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

def fake_state():
    fighter=dict(hp=400,x=200,energy=0,action='STAND',remainingActionFrames=0,canAct=True)
    return dict(frame=44,p1=fighter,p2={**fighter,'x':700})
class TestLockstep(unittest.TestCase):
    def test_both_get_same_menu_and_snapshot(self):
        gate=Barrier(2)
        def endpoint(url,state,menu):
            gate.wait(1)
            self.assertIn('Distance 500 px',state)
            self.assertEqual(list(menu),['DASH','FORWARD_WALK','FOR_JUMP'])
            return ('DASH' if url=='a' else 'FORWARD_WALK',100,0)
        with ThreadPoolExecutor(2) as pool:
            r=pair(pool,endpoint,['a','b'],fake_state(),0)
        self.assertEqual(r[0],['DASH','FORWARD_WALK'])
    def test_failure_does_not_advance(self):
        engine=type('E',(),{'step':lambda *_:self.fail('advanced without a valid response')})()
        def endpoint(url,*_):
            if url=='b': raise TimeoutError()
            return 'DASH',1,0
        with ThreadPoolExecutor(2) as pool:
            with self.assertRaises(TimeoutError):
                advance(engine,pool,endpoint,['a','b'],fake_state(),0)
    def test_both_colors_advance_in_same_call(self):
        calls=[]
        class E:
            def step(self,n,p1,p2):
                calls.append((n,p1,p2))
                return {'terminated':False}
        def endpoint(url,*_): return ('DASH' if url=='a' else 'FORWARD_WALK',1,0)
        with ThreadPoolExecutor(2) as pool:
            record,frames=advance(E(),pool,endpoint,['a','b'],fake_state(),0)
        self.assertEqual(sum(c[0] for c in calls),FORMAT)
        self.assertEqual({c[1:] for c in calls},{('DASH','FORWARD_WALK')})
        self.assertEqual(record['observedAtFrame'],44)
if __name__=='__main__':unittest.main()
