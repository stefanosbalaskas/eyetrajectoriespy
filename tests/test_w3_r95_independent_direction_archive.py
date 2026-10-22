"""Separate R95-A source-independent exact rational algebra gates."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import tempfile
import unittest
from scripts import audit_w3_r95_independent_direction_archive as a

class TestR95Audit(unittest.TestCase):
    def test_independent_sharp_population_regions(self):
        q0,q1=F(3,10),F(4,10);d=F(3,10)
        z=q1/(q0+q1)
        self.assertEqual(a.missing_mass_region(q0,q1,d,"unrestricted"),(q1,1-q0))
        self.assertEqual(a.missing_mass_region(q0,q1,d,"direction_unknown_union"),(q1,1-q0))
        self.assertEqual(a.missing_mass_region(q0,q1,d,"c1_at_least_c0"),(q1,z))
        self.assertEqual(a.missing_mass_region(q0,q1,d,"c0_at_least_c1"),(z,1-q0))
        self.assertEqual(a.missing_mass_region(q0,q1,d,"equal_completion"),(z,z))
        for delta in a.D:
            q=(1-delta)/2
            lo,hi=a.missing_mass_region(q,q,delta,"c1_ge_c0_ratio_le_1_plus_delta")
            self.assertTrue(q<lo<hi==F(1,2))
            x=a.endpoint(lo,q,q)
            self.assertEqual(a.frac(x["response_ratio_c1_over_c0"]),1+delta)

    def test_bad_and_missing_evidence_refused(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,"original archive"):
                a.verify_archive(Path(t))
        with self.assertRaisesRegex(ValueError,"noncanonical"):
            a.frac("2/4")
        with self.assertRaisesRegex(ValueError,"full 54-case"):
            a.replay([])
        with self.assertRaisesRegex(ValueError,"unspecified"):
            a.missing_mass_region(F(1,4),F(1,4),F(1,2),"unknown")

if __name__=="__main__":unittest.main()
