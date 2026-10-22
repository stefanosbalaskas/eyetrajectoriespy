"""R93 exact observed-likelihood equivalence and tamper fail-closed gates."""
from fractions import Fraction as F
from itertools import product
import json

import pytest

from scripts import prove_w3_r93_observed_equivalence as r93


def test_frozen_tiny_nonresponse_equivalence_exact_arithmetic():
    assert r93.EXPECTED_ROWS==27
    for d,g in product(r93.FAILURE_FRACTIONS,r93.INVITATION_FRACTIONS):
        a=r93.observed_law(d,g,"low_mean")
        b=r93.observed_law(d,g,"uniform_return")
        c=r93.observed_law(d,g,"high_mean")
        assert a==b==c
        assert sum(a.values())==1
        assert a["invited_nonresponse"]==g*d
        assert a["invited_responded_Z0"]==g*(1-d)/2
        assert a["invited_responded_Z1"]==g*(1-d)/2
        lo,hi=r93.exact_identified_set((1-d)/2,(1-d)/2)
        assert hi-lo==d
        assert r93.probability_world(d,"low_mean")["p1"]==lo
        assert r93.probability_world(d,"high_mean")["p1"]==hi
        assert r93.probability_world(d,"uniform_return")["p1"]==F(1,2)


def test_distinct_latent_response_laws_indistinguishable_even_given_invitation():
    for d in r93.FAILURE_FRACTIONS:
        low=r93.probability_world(d,"low_mean")
        mid=r93.probability_world(d,"uniform_return")
        high=r93.probability_world(d,"high_mean")
        assert len({low["p1"],mid["p1"],high["p1"]})==3
        assert low["c1"]==1 and high["c0"]==1
        assert low["c0"]==high["c1"]==(1-d)/(1+d)
        assert mid["c0"]==mid["c1"]==1-d
        assert low["c0"]<mid["c0"] and high["c1"]<mid["c1"]


def test_equal_likelihood_for_all_finite_observed_samples():
    for d in r93.FAILURE_FRACTIONS:
        for g in r93.INVITATION_FRACTIONS:
            p=r93.observed_law(d,g,"low_mean")
            q=r93.observed_law(d,g,"high_mean")
            for outcomes in product(tuple(p),repeat=3):
                pa=F(1)
                pb=F(1)
                for outcome in outcomes:
                    pa*=p[outcome]
                    pb*=q[outcome]
                assert pa==pb


def test_sharp_arbitrary_response_bounds_and_invalid_inputs():
    assert r93.exact_identified_set(F(3,10),F(4,10))==(F(4,10),F(7,10))
    for vals in [(F(0),F(1,2)),(F(1,2),F(0)),(F(3,4),F(1,2))]:
        with pytest.raises(ValueError,match="observed masses"):
            r93.exact_identified_set(*vals)
    with pytest.raises(ValueError,match="unregistered"):
        r93.probability_world(F(1,7),"uniform_return")
    with pytest.raises(ValueError,match="invitation"):
        r93.observed_law(F(1,100),F(1,3),"uniform_return")


def test_exact_records_detect_missing_or_tampered_source(tmp_path):
    obj=r93.evidence()
    assert obj["exact_rational_laws"]==27
    assert obj["nonidentification_even_at_99p9pct_return"]
    rows=obj["records"]
    assert r93.verify(rows)
    with pytest.raises(ValueError,match="full source ledger"):
        r93.verify(rows[:-1])
    damaged=json.loads(json.dumps(rows))
    damaged[1]["latent_mean_binary_Z"]="999/1000"
    with pytest.raises(ValueError,match="altered"):
        r93.verify(damaged)
    r93.main  # direct CI runs the output CLI and validates SHA256 evidence separately
