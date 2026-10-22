"""Exact R95 analytical controls; no package or gaze data needed."""
from fractions import Fraction as F
from itertools import product
import copy
import unittest
from scripts import prove_w3_r95_monotone_return_direction as r

class TestR95(unittest.TestCase):
    def test_general_asymmetric_observed_law(self):
        q0,q1=F(3,10),F(4,10)
        center=q1/(q0+q1)
        self.assertEqual(r.sharp_interval(q0,q1,"unrestricted"),(q1,1-q0))
        self.assertEqual(r.sharp_interval(q0,q1,"c1_at_least_c0"),(q1,center))
        self.assertEqual(r.sharp_interval(q0,q1,"c0_at_least_c1"),(center,1-q0))
        self.assertEqual(r.sharp_interval(q0,q1,"equal_completion"),(center,center))
        self.assertEqual(r.sharp_interval(q0,q1,"direction_unknown_union"),(q1,1-q0))
        with self.assertRaisesRegex(ValueError,"exact cap"):
            r.sharp_interval(q0,q1,"c1_ge_c0_ratio_le_1_plus_delta")
        with self.assertRaisesRegex(TypeError,"exact rational"):
            r.sharp_interval(0.3,q1,"unrestricted")

    def test_likelihoods_identical_across_assumptions(self):
        self.assertTrue(r.verify(r.rows()))
        for d,g in product(r.FAILURES,r.INVITATIONS):
            cell=[x for x in r.rows() if x["invited_nonreturn"]==r.canonical(d) and x["known_random_invitation"]==r.canonical(g)]
            self.assertEqual(len(cell),6)
            self.assertEqual(len({str(y["observed_joint_law"]) for y in cell}),1)
            self.assertEqual(F(next(y for y in cell if y["external_direction_assumption"]=="c1_at_least_c0")["sharp_width"]),d/2)

    def test_endpoint_witness_and_tamper_fail_closed(self):
        records=r.rows()
        for row in records:
            q=F(row["observed_conditional_q0"])
            a=row["external_direction_assumption"]
            d=F(row["invited_nonreturn"])
            for key in ("lower_endpoint_witness","upper_endpoint_witness"):
                w=row[key]
                self.assertEqual(r.point_witness(F(w["p"]),q,q,a,d),w)
        altered=copy.deepcopy(records)
        altered[7]["sharp_width"]="1/7"
        with self.assertRaisesRegex(ValueError,"altered"):
            r.verify(altered)
        with self.assertRaisesRegex(ValueError,"complete"):
            r.verify(records[1:])

if __name__=="__main__": unittest.main()
