"""Independent arithmetic identities and adversarial R94 source integrity tests."""
import json
from fractions import Fraction as F
from itertools import product
import unittest
from scripts import prove_w3_r94_external_completion_floors as r94


class TestExternalFloorSets(unittest.TestCase):
    def test_numeric_sharp_interval_formula_and_endpoint_witnesses(self):
        q=F(99,200)
        self.assertEqual(r94.sharp_set(q,q),(q,1-q))
        self.assertEqual(r94.sharp_set(q,q,F(99,100),F(99,100)),(F(1,2),F(1,2)))
        self.assertEqual(r94.sharp_set(q,q,F(199,200),F(199,200)),None)
        self.assertEqual(r94.sharp_set(q,q,F(99,100),F(49,50)),(F(1,2),F(101,200)))
        for d,g,s in product(r94.DELTA,r94.INVITATIONS,r94.SCENARIOS):
            q=(1-d)/2
            f0,f1=r94.response_floors(d,s)
            region=r94.sharp_set(q,q,f0,f1)
            if region:
                for p in (region[0],(region[0]+region[1])/2,region[1]):
                    r94.witnessed_model(p,q,q,f0,f1)

    def test_contradictory_and_invalid_laws(self):
        with self.assertRaisesRegex(ValueError,"invalid observed"):
            r94.sharp_set(F(3,4),F(1,2))
        with self.assertRaisesRegex(ValueError,"invalid observed"):
            r94.sharp_set(F(1,4),F(1,4),F(11,10),F(1,2))
        with self.assertRaises(TypeError):
            r94.sharp_set(0.4,F(1,2))
        with self.assertRaisesRegex(ValueError,"unregistered"):
            r94.response_floors(F(1,3),"unrestricted")

    def test_frozen_factorial_and_tamper_detection(self):
        rows=r94.construct_rows()
        self.assertEqual(len(rows),54)
        self.assertTrue(r94.verify(rows))
        obj=json.loads(json.dumps(rows))
        with self.assertRaisesRegex(ValueError,"full evidence"):
            r94.verify(obj[:-1])
        obj=json.loads(json.dumps(rows))
        obj[5]["sharp_lower"]="0/1"
        with self.assertRaisesRegex(ValueError,"altered"):
            r94.verify(obj)
        self.assertTrue(all(not z["release_authorized"] for z in rows))

    def test_invitation_does_not_change_conditional_sharp_set(self):
        for d,s in product(r94.DELTA,r94.SCENARIOS):
            r=[x for x in r94.construct_rows() if x["failure_among_invited"]==r94.rational(d) and x["external_assumption"]==s]
            self.assertEqual(len(r),3)
            self.assertEqual(len(set((z["sharp_lower"],z["sharp_upper"]) for z in r)),1)


if __name__=="__main__":
    unittest.main()
