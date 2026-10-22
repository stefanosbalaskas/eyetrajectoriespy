"""R94-A source-independent mathematical rederivation and fail-closed contracts."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import tempfile
import unittest
from scripts import audit_w3_r94_external_floor_archive_independent as a

class TestAudit(unittest.TestCase):
    def test_missing_outcome_mass_allocation(self):
        q=F(99,200)
        self.assertEqual(a.missing_outcome_allocation(q,q,F(0),F(0)),(q,1-q))
        self.assertEqual(a.missing_outcome_allocation(q,q,F(99,100),F(99,100)),(F(1,2),F(1,2)))
        self.assertIsNone(a.missing_outcome_allocation(q,q,F(199,200),F(199,200)))
        self.assertEqual(a.missing_outcome_allocation(q,q,F(99,100),F(49,50)),(F(1,2),F(101,200)))
        with self.assertRaisesRegex(ValueError,"invalid source"):
            a.missing_outcome_allocation(F(9,10),F(9,10),F(0),F(0))

    def test_independent_floor_contrasts(self):
        for d,g,s in product(a.DELTA,a.G,a.CASES):
            q=(1-d)/2
            floor=a.design_floors(d,s)
            x=a.missing_outcome_allocation(q,q,*floor)
            if s=="overstrong_incompatible":self.assertIsNone(x)
            else:
                self.assertIsNotNone(x)
                for p in x:
                    model=a.witness_for(p,q,q)
                    self.assertTrue(floor[0]<=a.decode(model["c0"])<=1)
                    self.assertTrue(floor[1]<=a.decode(model["c1"])<=1)

    def test_missing_manifest_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"complete immutable"):
                a.verify_archive(Path(d))
        with self.assertRaisesRegex(ValueError,"non-rational"):
            a.decode("0.9")
        with self.assertRaisesRegex(ValueError,"unnormalized"):
            a.decode("2/4")

if __name__=="__main__":unittest.main()
