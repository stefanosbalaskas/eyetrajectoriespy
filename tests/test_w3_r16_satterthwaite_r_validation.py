"""R16 independent R clubSandwich Satterthwaite df and interval comparator.

Runs ONLY when EYE_SATTERTHWAITE_REQUIRE_R=1 in dedicated R-equipped CI.
No release, API promotion, or coverage-selection threshold.
"""
import os
import shutil
import subprocess

import numpy as np
import pytest
from scipy.stats import t as student_t

from scripts.w3_r16_cr2_correlated_target import cr2_correlated_wls
from scripts.w3_r16_cr2_satterthwaite_reference import cr2_satterthwaite_reference


def design(n=12, unequal=False, extreme=False, rho=.0):
    counts=np.array([2+(i%3) for i in range(n)]) if unequal else np.full(n,3)
    persons=np.repeat(np.arange(n),counts)
    x_person=np.linspace(-.8,.8,n)
    if extreme:
        x_person[0]=3.0
        x_person[1]=-2.5
    x=x_person[persons]
    time=np.concatenate([np.linspace(.1,.9,int(z)) for z in counts])
    idx=np.arange(len(x))
    y=.2+.7*x-.12*time+.17*x*time+.05*np.sin(1.3*idx)
    X=np.column_stack([np.ones(len(x)),x,time,x*time])
    targets=[(1-rho)*np.eye(int(m))+rho*np.ones((int(m),int(m))) for m in counts]
    return X,y,persons,targets


@pytest.mark.parametrize("unequal,extreme,rho",[
    (False,False,0.),(False,False,.4),
    (True,False,.4),(True,True,0.),(True,True,.4),
])
def test_external_satterthwaite_df_and_critical_value(unequal,extreme,rho):
    if os.getenv("EYE_SATTERTHWAITE_REQUIRE_R")!="1":
        pytest.skip("External R oracle runs in the dedicated workflow only")
    if shutil.which("Rscript") is None:
        pytest.fail("Rscript is mandatory for the dedicated independent reference")
    X,y,groups,targets=design(12,unequal,extreme,rho)
    n=len(np.unique(groups))
    contrasts=[np.array([0.,1.,0.,.5]),np.array([0.,0.,1.,0.])]
    py=[]
    for c in contrasts:
        mom=cr2_satterthwaite_reference(X,np.ones(len(y)),groups,c,targets)
        cov=cr2_correlated_wls(X,y,np.ones(len(y)),groups,c,targets)
        df=mom["df"];se=cov["cr2_se"]
        py.append((df,se,float(student_t.ppf(.95,df)),float(cov["point"])))
    rcode="""
    suppressPackageStartupMessages(library(clubSandwich))
    n <- 12
    unequal <- __UNEQUAL__
    extreme <- __EXTREME__
    rho <- __RHO__
    sizes <- if (unequal) 2L + ((seq_len(n)-1L) %% 3L) else rep(3L,n)
    grp <- rep(seq_len(n),times=sizes)
    xp <- seq(-.8,.8,length.out=n)
    if (extreme) { xp[1] <- 3; xp[2] <- -2.5 }
    x <- xp[grp]
    time <- unlist(lapply(sizes,function(m) seq(.1,.9,length.out=m)))
    idx <- 0:(length(x)-1)
    y <- .2+.7*x-.12*time+.17*x*time+.05*sin(1.3*idx)
    fit <- lm(y ~ x*time)
    target <- lapply(sizes,function(m) (1-rho)*diag(m)+rho*matrix(1,m,m))
    V <- vcovCR(fit, cluster=grp, type="CR2", target=target, inverse_var=TRUE)
    contrasts <- rbind(c(0,1,0,.5), c(0,0,1,0))
    out <- linear_contrast(fit,vcov=V,contrasts=contrasts,
                           level=.90,test="Satterthwaite")
    for (i in seq_len(nrow(out))) {
      df <- as.numeric(out[["d.f."]][i])
      se <- as.numeric(out[["SE"]][i])
      est <- as.numeric(out[["Estimate"]][i])
      critical <- qt(.95,df)
      cat(sprintf("R16REF %.16g %.16g %.16g %.16g\\n",df,se,critical,est))
    }
    """
    rcode=(rcode.replace("__UNEQUAL__", "TRUE" if unequal else "FALSE")
               .replace("__EXTREME__", "TRUE" if extreme else "FALSE")
               .replace("__RHO__", format(rho, ".17g")) )
    run=subprocess.run(["Rscript","-e",rcode],capture_output=True,
                        text=True,check=True)
    records=[line.split()[1:] for line in run.stdout.splitlines()
             if line.startswith("R16REF ")]
    assert len(records)==len(contrasts),run.stdout+"\n"+run.stderr
    for observed,reference in zip(py,records):
        np.testing.assert_allclose(observed,np.array(reference,float),
                                   rtol=2e-6,atol=2e-8)
