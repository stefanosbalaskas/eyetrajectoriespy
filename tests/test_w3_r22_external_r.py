"""R22 independent external clubSandwich comparator for correlated targets.

This test MUST run in R-equipped CI and fail if R is unavailable.
It compares both CR2 standard errors and contrast-specific Satterthwaite df,
not just adjustment matrix identities or variance positivity.
"""
import os
import shutil
import subprocess
import numpy as np
import pytest
from scipy.stats import t as student_t

from scripts.w3_r22_scaled_cholesky_cr2 import stable_cr2_blockwise_wls


@pytest.mark.parametrize("unequal,extreme,rho",[
    (False,False,0.0),
    (True,False,.4),
    (False,True,.4),
    (True,True,.4),
])
def test_scaled_cholesky_matches_independent_r_clubsandwich(unequal,extreme,rho):
    if os.environ.get("EYE_R22_REQUIRE_EXTERNAL_R")!="1":
        pytest.skip("Independent R validation occurs in dedicated workflow")
    if shutil.which("Rscript") is None:
        pytest.fail("Mandatory Rscript absent in independent scientific CI")
    n=12
    sizes=np.asarray([2+i%3 for i in range(n)]) if unequal else np.full(n,3)
    groups=np.repeat(np.arange(n),sizes)
    xp=np.linspace(-.8,.8,n)
    if extreme:
        xp[0]=3.;xp[1]=-2.5
    x=xp[groups]
    time=np.concatenate([np.linspace(.1,.9,int(k)) for k in sizes])
    idx=np.arange(len(x))
    y=.2+.7*x-.12*time+.17*x*time+.05*np.sin(1.3*idx)
    X=np.column_stack([np.ones(len(x)),x,time,x*time])
    target=[(1-rho)*np.eye(int(k))+rho*np.ones((int(k),int(k))) for k in sizes]
    contrasts=(np.array([0.,1.,0.,.5]),np.array([0.,0.,1.,0.]))
    found=[]
    for c in contrasts:
        obj=stable_cr2_blockwise_wls(
            X,y,np.ones(len(y)),groups,c,target)
        nu=obj["satterthwaite_df"]
        found.append((nu,obj["cr2_se"],float(student_t.ppf(.95,nu)),
                      obj["point"]))
        assert obj["max_relative_adjustment_identity_error"]<3e-7
    rscript="""
    suppressPackageStartupMessages(library(clubSandwich))
    n<-12
    unequal<-__UNEQUAL__
    extreme<-__EXTREME__
    rho<-__RHO__
    sizes<-if(unequal) 2L+((seq_len(n)-1L)%%3L) else rep(3L,n)
    grp<-rep(seq_len(n),times=sizes)
    xp<-seq(-.8,.8,length.out=n)
    if(extreme){xp[1]<-3;xp[2]<--2.5}
    x<-xp[grp]
    time<-unlist(lapply(sizes,function(m)seq(.1,.9,length.out=m)))
    idx<-0:(length(x)-1)
    y<-.2+.7*x-.12*time+.17*x*time+.05*sin(1.3*idx)
    fit<-lm(y~x*time)
    target<-lapply(sizes,function(m)(1-rho)*diag(m)+rho*matrix(1,m,m))
    V<-vcovCR(fit,cluster=grp,type="CR2",target=target,inverse_var=FALSE)
    out<-linear_contrast(fit,vcov=V,
        contrasts=rbind(c(0,1,0,.5),c(0,0,1,0)),
        level=.90,test="Satterthwaite")
    stopifnot(nrow(out)==2L,all(c("df","SE","Est")%in%names(out)))
    for(i in seq_len(nrow(out)))cat(sprintf(
        "R22REF %.16g %.16g %.16g %.16g\\n",
        as.numeric(out[["df"]][i]),as.numeric(out[["SE"]][i]),
        qt(.95,as.numeric(out[["df"]][i])),
        as.numeric(out[["Est"]][i])))
    """
    rscript=(rscript.replace("__UNEQUAL__","TRUE" if unequal else "FALSE")
            .replace("__EXTREME__","TRUE" if extreme else "FALSE")
            .replace("__RHO__",format(rho,".17g")))
    run=subprocess.run(["Rscript","-e",rscript],text=True,capture_output=True,
                       check=True)
    refs=[line.split()[1:] for line in run.stdout.splitlines()
          if line.startswith("R22REF ")]
    assert len(refs)==len(found),run.stdout+"\n"+run.stderr
    np.testing.assert_allclose(np.asarray(found,float),
                               np.asarray(refs,float),
                               rtol=2e-6,atol=2e-8)
