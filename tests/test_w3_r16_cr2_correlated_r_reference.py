"""Independent correlated-target CR2 comparison with R clubSandwich."""
import os
import shutil
import subprocess
import numpy as np
import pytest
from scripts.w3_r16_cr2_correlated_target import cr2_correlated_wls

def test_correlated_working_target_against_r_clubsandwich():
    if os.getenv("EYE_CR2_REQUIRE_R_REFERENCE")!="1":
        pytest.skip("Dedicated R CI required")
    if shutil.which("Rscript") is None:
        pytest.fail("Rscript required for external CR2 validation")
    n=12
    x=np.repeat(np.linspace(-.8,.8,n),3)
    t=np.tile([.1,.5,.9],n)
    X=np.column_stack([np.ones(len(x)),x,t,x*t])
    row=np.arange(len(x))
    y=.2+.7*x-.12*t+.17*x*t+.05*np.sin(1.3*row)
    corr=.4
    target=[(1-corr)*np.eye(3)+corr*np.ones((3,3)) for _ in range(n)]
    c=np.array([0.,1.,0.,.5])
    ours=cr2_correlated_wls(X,y,np.ones(len(y)),np.repeat(np.arange(n),3),c,target)
    script="""
    suppressPackageStartupMessages(library(clubSandwich))
    n <- 12
    idx <- 0:(n*3-1)
    x <- rep(seq(-.8,.8,length.out=n),each=3)
    t <- rep(c(.1,.5,.9),times=n)
    y <- .2+.7*x-.12*t+.17*x*t+.05*sin(1.3*idx)
    fit <- lm(y ~ x*t)
    phi <- lapply(seq_len(n), function(z) (1-.4)*diag(3)+.4*matrix(1,3,3))
    vc <- vcovCR(fit, cluster=rep(seq_len(n),each=3), type="CR2",
                 target=phi, inverse_var=FALSE)
    h <- c(0,1,0,.5)
    cat(sprintf("%.16g",sqrt(drop(t(h) %*% vc %*% h))))
    """
    out=subprocess.run(["Rscript","-e",script],capture_output=True,text=True,check=True)
    expected=float(out.stdout.strip())
    np.testing.assert_allclose(ours["cr2_se"],expected,atol=1e-8,rtol=1e-7)
    assert ours["covariance_adjustment_error"]<1e-8
