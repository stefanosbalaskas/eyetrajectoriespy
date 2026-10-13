"""Cross-language CR2 numerical contract against R clubSandwich."""
import subprocess
import shutil
import pytest
import numpy as np
from scripts.w3_r16_cr2_reference import cr2_wls_identity

def test_against_r_clubsandwich_unweighted():
    if shutil.which('Rscript') is None:
        pytest.skip('Rscript not installed; cross-language contract runs in dedicated R CI')
    n=24
    rows=np.arange(n*3)
    x=np.repeat(np.linspace(-.8,.8,n),3)
    t=np.tile([.1,.5,.9],n)
    X=np.column_stack([np.ones(len(x)),x,t,x*t])
    y=.2+.7*x-.12*t+.17*x*t+.05*np.sin(1.3*rows)
    c=np.array([0.,1.,0.,.5])
    py=cr2_wls_identity(X,y,np.ones(len(y)),np.repeat(np.arange(n),3),c)
    code="""
    suppressPackageStartupMessages(library(clubSandwich))
    n <- 24
    idx <- 0:(n*3-1)
    x <- rep(seq(-.8,.8,length.out=n),each=3)
    t <- rep(c(.1,.5,.9),times=n)
    y <- .2+.7*x-.12*t+.17*x*t+.05*sin(1.3*idx)
    fit <- lm(y ~ x*t)
    vc <- vcovCR(fit, cluster=rep(seq_len(n),each=3), type="CR2",
                 target=rep(1,length(y)),inverse_var=TRUE)
    h <- c(0,1,0,.5)
    cat(sprintf("%.16g",sqrt(drop(t(h) %*% vc %*% h))))
    """
    r=subprocess.run(["Rscript","-e",code],capture_output=True,text=True,check=True)
    actual=float(r.stdout.strip())
    np.testing.assert_allclose(py["cr2_se"],actual,rtol=5e-8,atol=5e-10)
