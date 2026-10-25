// Independent, non-deploying repeated Lighthouse evidence, not a release criterion.
// CI uses only local static build files; no Lighthouse report is uploaded to a
// remote service. Three runs per route show simulated run-to-run variation.
module.exports = {
  ci: {
    collect: {
      staticDistDir: "./build/lighthouse-webroot",
      url: [
        "http://localhost/eyetrajectoriespy/",
        "http://localhost/eyetrajectoriespy/start/first-analysis/",
        "http://localhost/eyetrajectoriespy/tools/figure-storyboard/",
        "http://localhost/eyetrajectoriespy/integrations/navigator/",
      ],
      numberOfRuns: 3,
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
