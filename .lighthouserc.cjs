// Independent, non-deploying Lighthouse baseline, not a release criterion.
// CI uses only local static build files; no Lighthouse report is uploaded to a
// remote service. Review variation across more than one run before budgets.
module.exports = {
  ci: {
    collect: {
      staticDistDir: "./site",
      url: [
        "http://localhost:0/",
      ],
      numberOfRuns: 1,
      settings: {
        onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
        formFactor: "mobile",
        throttlingMethod: "simulate",
        chromeFlags: "--no-sandbox --disable-dev-shm-usage",
      },
    },
    upload: { target: "filesystem", outputDir: "build/lighthouse-audit" },
  },
};
