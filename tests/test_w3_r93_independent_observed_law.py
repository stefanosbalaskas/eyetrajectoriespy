"""R93-A independently derived rational observed likelihood and artifact gates."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path

import pytest

from scripts import audit_w3_r93_exact_observed_law_independent as a


def test_source_agnostic_latent_identification_exact():
    assert a.EXPECTED==27
    for d,g in product(a.DELTA,a.G):
        low=a.expected_row(d,g,"low_mean")
        mid=a.expected_row(d,g,"uniform_return")
        high=a.expected_row(d,g,"high_mean")
        assert low["observed"]==mid["observed"]==high["observed"]
        assert sum(low["observed"].values())==F(1)
        assert low["p1"]<mid["p1"]<high["p1"]
        assert high["p1"]-low["p1"]==d
        assert mid["c0"]==mid["c1"]==1-d
        assert low["c1"]==high["c0"]==1
        assert low["c0"]==high["c1"]==(1-d)/(1+d)
        assert low["observed"]["invited_nonresponse"]==g*d


def test_known_invitation_does_not_identify_binary_mean():
    d=F(1,1000)
    for g in a.G:
        w0=a.expected_row(d,g,"low_mean")
        w1=a.expected_row(d,g,"high_mean")
        assert w0["observed"]==w1["observed"]
        assert w0["p1"]==F(999,2000)
        assert w1["p1"]==F(1001,2000)


def test_exact_observed_product_likelihood_for_multiple_length_sequences():
    for d,g in product(a.DELTA,a.G):
        low=a.expected_row(d,g,"low_mean")["observed"]
        high=a.expected_row(d,g,"high_mean")["observed"]
        for seq in product(a.EVENTS,repeat=4):
            def likelihood(m):
                p=F(1)
                for v in seq:
                    p*=m[v]
                return p
            assert likelihood(low)==likelihood(high)


def test_source_wire_rationals_and_fail_closed_archive():
    assert a.frac("0/1")==F(0)
    assert a.frac("1/1")==F(1)
    assert a.frac("999/1000")==F(999,1000)
    with pytest.raises(ValueError,match="noncanonical"):
        a.frac("2/4")
    with pytest.raises(ValueError,match="rational"):
        a.frac("0.5")
    with pytest.raises(ValueError,match="archive required"):
        a.verify_archive(Path("/no/original-r93/source"))
    with pytest.raises(ValueError,match="ledger incomplete"):
        a.validate_archived_records([])
