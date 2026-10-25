/* Researcher-facing integration discovery. No requests, analytics, or remote code.
   A documentation navigator, NOT an importer, dependency resolver or validator.
   All links and claims are maintained as finite literal catalog entries.
*/
(function (factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (typeof document !== "undefined") {
    const mount = function () { api.init(document, window); };
    if (typeof document$ !== "undefined" && document$ && typeof document$.subscribe === "function") {
      document$.subscribe(mount);
    } else if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", mount);
    } else {
      mount();
    }
  }
})(function () {
  "use strict";
  const CATALOG = Object.freeze([
    {id:"table", name:"pandas / Polars / PyArrow", group:"tables", phase:"example", device:"general",
      summary:"Explicitly map long-format tables and Parquet sources; refuse invented dense support.",
      guide:"../tabular-handoff/", upstream:"https://docs.pola.rs/", route:"Tabular schema → source mapping → observed support audit.",
      boundary:"Repository example only; no new released importer or implicit coordinate conversion."},
    {id:"pymovements", name:"pymovements", group:"acquisition", phase:"preview", device:"general",
      summary:"Use upstream gaze samples with nested coordinate channels and explicit millisecond time.",
      guide:"../pymovements-handoff/", upstream:"https://pymovements.readthedocs.io/en/stable/",
      route:"Gaze.samples → mapped participant/trial/time/eye units → canonical samples.",
      boundary:"Pinned 0.28.0 synthetic-object CI; recorded-device compatibility not qualified."},
    {id:"syelink", name:"SyeLink", group:"acquisition", phase:"preview", device:"eyelink",
      summary:"Convert explicitly selected-eye EyeLink ASC session samples without dropping segment provenance.",
      guide:"../syelink-handoff/", upstream:"https://syelink.readthedocs.io/en/latest/",
      route:"EyeLink ASC → RECORD samples by segment/eye → original millisecond clock.",
      boundary:"Pinned 2.0.0 dataclass CI; real EyeLink ASC accuracy not qualified."},
    {id:"bids", name:"Eye-Tracking-BIDS", group:"standards", phase:"preview", device:"general",
      summary:"Read-only sidecar and bounded compressed-TSV shape inspection.",
      guide:"../bids-metadata-inspector/", upstream:"https://bids-specification.readthedocs.io/en/stable/",
      route:"BIDS physio JSON + TSV.GZ → provenance inspection; no raw gaze import.",
      boundary:"Restricted metadata example, not official BIDS conformance or device validation."},
    {id:"pyneon", name:"PyNeon", group:"acquisition", phase:"planned", device:"neon",
      summary:"Candidate Neon-native, cloud, epoch and multimodal recordings handoff.",
      guide:"../acquisition-and-bids/", upstream:"https://ncc-brain.github.io/PyNeon/",
      route:"Neon source → time/coordinate and trial provenance → future explicit table mapping.",
      boundary:"Documentation only: no direct PyNeon adapter has been qualified."},
    {id:"eye2bids", name:"eye2bids", group:"standards", phase:"planned", device:"general",
      summary:"Candidate exporter for supported devices and BIDS-oriented provenance.",
      guide:"../acquisition-and-bids/", upstream:"https://github.com/bids-standard/eye2bids",
      route:"Device recording → source-preserving BIDS conversion → inspect sidecars separately.",
      boundary:"Upstream exporter; no supported eyetrajectoriespy coupling."},
    {id:"eyelinkio", name:"EyeLinkIO", group:"acquisition", phase:"comparison", device:"eyelink",
      summary:"Potential EDF reader for comparison with ASC extraction.",
      guide:"../eyelink-ecosystem/", upstream:"https://pypi.org/project/eyelinkio/",
      route:"EDF binary reader → independent timestamp/sample comparison with ASC.",
      boundary:"Not tested as an adapter; independent real-device evidence required."},
    {id:"pyelink", name:"PyeLink", group:"acquisition", phase:"comparison", device:"eyelink",
      summary:"Hardware acquisition/control context, not a functional statistical engine.",
      guide:"../eyelink-ecosystem/", upstream:"https://pyelink.readthedocs.io/en/latest/",
      route:"EyeLink hardware control → vendor recording → separately auditable export.",
      boundary:"Hardware/SDK workflow; never a required package dependency."},
    {id:"pandera", name:"Pandera", group:"tables", phase:"planned", device:"general",
      summary:"Optional data-schema validators for explicit nullability and type checks.",
      guide:"../roadmap/", upstream:"https://pandera.readthedocs.io/en/stable/",
      route:"Source dataframe → schema validation → explicit canonical table.",
      boundary:"Proposed only; default package dependencies unchanged."},
    {id:"eyekit", name:"eyekit", group:"companion", phase:"comparison", device:"general",
      summary:"Reading text interest areas and fixation analysis alongside trajectories.",
      guide:"../acquisition-and-bids/", upstream:"https://pypi.org/project/eyekit/",
      route:"Reading fixation/IA outcomes kept distinct from raw time-indexed gaze.",
      boundary:"Companion methods; no direct importer or AOI semantic equivalence."},
    {id:"pupeyes", name:"PupEyes", group:"companion", phase:"comparison", device:"general",
      summary:"Pupillometry preprocessing and review without replacing gaze samples.",
      guide:"../acquisition-and-bids/", upstream:"https://pupeyes.readthedocs.io/en/latest/",
      route:"Pupil and blink signals → preserve masks/clock and modality provenance.",
      boundary:"Companion only; no claimed cross-clock synchronization."},
    {id:"scikit-fda", name:"scikit-fda", group:"functional", phase:"optional", device:"general",
      summary:"Existing optional functional-data library for representations and reference analyses.",
      guide:"../../guides/basis-representations/", upstream:"https://fda.readthedocs.io/en/stable/",
      route:"Qualified functional representation → opt-in reference analysis.",
      boundary:"Existing optional extra; numerical agreement is not inferential calibration."},
    {id:"fdapy", name:"FDApy", group:"functional", phase:"optional", device:"general",
      summary:"Existing optional sparse functional smoothing and FPCA reference routes.",
      guide:"../../guides/sparse-irregular-fpca/", upstream:"https://fdapy.readthedocs.io/en/latest/",
      route:"Native sparse observations → explicitly configured optional FDApy reference.",
      boundary:"Existing optional extra with Python-version constraints; not a new integration."},
    {id:"fdasrsf", name:"fdasrsf", group:"functional", phase:"optional", device:"general",
      summary:"Existing opt-in elastic-function analysis dependency.",
      guide:"../../guides/elastic-trajectories/", upstream:"https://pypi.org/project/fdasrsf/",
      route:"Functional curves → elastic comparison only under declared registration assumptions.",
      boundary:"Existing optional extra; phase alignment decisions must be reported."}
  ]);
  const PHASES = Object.freeze({
    example:"Repository example", preview:"Pinned preview", optional:"Existing optional extra",
    planned:"Research candidate", comparison:"External companion / comparison"
  });
  const SUPPORT = Object.freeze({
    unknown: {label:"Not established", description:"Identify the actual recorded support before using any functional estimator.",
      link:"../../start/data-to-method/", note:"Do not infer uniform samples from nominal device frequency."},
    aligned: {label:"Complete common grid", description:"Check original within-trial times, x/y completeness, participant independence and preprocessing history.",
      link:"../../workflows/fpca-exploration/", note:"Only truly aligned recorded support is compatible with a dense starting point."},
    sparse: {label:"Paired sparse / irregular", description:"Retain recorded native timestamps and gaps; inspect paired sparse methods without resampling to a dense grid.",
      link:"../../guides/sparse-multivariate-fpca/", note:"Shared x/y observed times must genuinely exist; no gap filling by default."},
    async: {label:"Asynchronous x/y", description:"Retain coordinate-specific clocks and separate observation masks.",
      link:"../../guides/irregular-trajectories/", note:"Nearest-neighbor fabricated simultaneous pairs are not observed gaze."},
    repeated: {label:"Repeated participant trials", description:"Preserve participant clusters, trial keys and design alignment before selecting a repeated-effects method.",
      link:"../../workflows/repeated-trial-mixed-effects/", note:"The trial is not automatically an independent participant."}
  });
  function catalog() { return CATALOG.map(x => Object.assign({}, x)); }
  function filterCatalog(query, group, phase) {
    const q = String(query || "").trim().toLocaleLowerCase();
    return CATALOG.filter(x =>
      (!group || group === "all" || x.group === group) &&
      (!phase || phase === "all" || x.phase === phase) &&
      (!q || [x.name, x.summary, x.route, x.boundary, x.group, x.device].join(" ").toLocaleLowerCase().includes(q))
    );
  }
  function planFor(sourceId, supportId) {
    const source = CATALOG.find(x => x.id === sourceId) || CATALOG[0];
    const support = SUPPORT[supportId] || SUPPORT.unknown;
    const steps = [
      "Preserve original device/export files and upstream parser or package version.",
      "Record participant ID, trial mapping, timestamp origin/unit, coordinate system, eye and upstream event/preprocessing history.",
      source.route,
      support.description,
      "Audit missing/invalid samples and independent experimental units; do not equate import success with scientifically valid inference."
    ];
    return {
      source:source.id, sourceName:source.name, phase:PHASES[source.phase],
      guide:source.guide, upstream:source.upstream, boundary:source.boundary,
      support:support.label, supportGuide:support.link, supportNote:support.note,
      steps:steps,
      text:"Source: "+source.name+" ("+PHASES[source.phase]+")\nRecorded support: "+support.label+
           "\n\n"+steps.map((s,i)=>(i+1)+". "+s).join("\n")+
           "\n\nIntegration boundary: "+source.boundary+"\nSupport boundary: "+support.note+
           "\nThis planner is documentation only: no file was processed or validated."
    };
  }
  function validState(q) {
    const p = new URLSearchParams(q);
    const id = p.get("et_source");
    const support = p.get("et_support");
    return {
      source:CATALOG.some(x=>x.id===id)?id:"table",
      support:Object.prototype.hasOwnProperty.call(SUPPORT,support)?support:"unknown"
    };
  }
  function shareUrl(href, source, support) {
    const url = new URL(href);
    const state = planFor(source,support);
    url.searchParams.set("et_source",state.source);
    const key = Object.prototype.hasOwnProperty.call(SUPPORT,support)?support:"unknown";
    url.searchParams.set("et_support",key);
    return url;
  }
  function init(doc, win) {
    const host = doc.getElementById("et-integration-navigator");
    if (!host || host.dataset.initialized) return;
    host.dataset.initialized = "1";
    const search = host.querySelector("#et-package-search");
    const group = host.querySelector("#et-package-group");
    const phase = host.querySelector("#et-package-phase");
    const grid = host.querySelector("#et-package-grid");
    const count = host.querySelector("#et-package-count");
    const fallback = host.querySelector("#et-package-fallback");
    const source = host.querySelector("#et-path-source");
    const support = host.querySelector("#et-path-support");
    const summary = host.querySelector("#et-path-summary");
    const steps = host.querySelector("#et-path-steps");
    const guide = host.querySelector("#et-path-guide");
    const method = host.querySelector("#et-path-method");
    const limitation = host.querySelector("#et-path-limitation");
    const copy = host.querySelector("#et-path-copy");
    const share = host.querySelector("#et-path-share");
    const status = host.querySelector("#et-path-status");
    let currentPlan = null;
    function element(tag, value, cls) {
      const e = doc.createElement(tag);
      if (value !== undefined) e.textContent=value;
      if (cls) e.className=cls;
      return e;
    }
    function card(item) {
      const el=element("article",undefined,"et-connect-card");
      const header=element("div",undefined,"et-connect-card-head");
      header.append(element("h3",item.name),element("span",PHASES[item.phase],"et-connect-status"));
      el.append(header,element("p",item.summary),element("p",item.boundary,"et-connect-boundary"));
      const links=element("div",undefined,"et-connect-links");
      const internal=element("a","Integration guide");
      internal.href=new URL(item.guide,win.location.href).href;
      const external=element("a","Upstream docs");
      external.href=item.upstream;external.target="_blank";external.rel="noopener noreferrer";
      links.append(internal,external);el.append(links);
      return el;
    }
    function renderCatalog() {
      const items=filterCatalog(search.value,group.value,phase.value);
      const fragment=doc.createDocumentFragment();
      items.forEach(item=>fragment.append(card(item)));
      grid.replaceChildren(fragment);
      count.textContent=items.length+" of "+CATALOG.length+" integrations displayed";
      host.querySelector("#et-empty-results").hidden=items.length!==0;
    }
    function writePlan() {
      currentPlan=planFor(source.value,support.value);
      summary.textContent=currentPlan.sourceName+" · "+currentPlan.phase+" · "+currentPlan.support;
      const fragment=doc.createDocumentFragment();
      currentPlan.steps.forEach(s=>fragment.append(element("li",s)));
      steps.replaceChildren(fragment);
      guide.href=new URL(currentPlan.guide,win.location.href).href;
      method.href=new URL(currentPlan.supportGuide,win.location.href).href;
      limitation.textContent="Research boundary: "+currentPlan.boundary+" "+currentPlan.supportNote;
      const url=shareUrl(win.location.href,source.value,support.value);
      win.history.replaceState(win.history.state,"",url.pathname+url.search+url.hash);
      status.textContent="Updated source-to-method checklist. No file was read or uploaded.";
    }
    host.querySelector("#et-package-reset").addEventListener("click",()=>{
      search.value="";group.value="all";phase.value="all";renderCatalog();search.focus();
    });
    [search,group,phase].forEach(c=>c.addEventListener(c===search?"input":"change",renderCatalog));
    [source,support].forEach(c=>c.addEventListener("change",writePlan));
    copy.addEventListener("click",async()=>{
      if (!currentPlan) return;
      try {
        if (!win.navigator.clipboard || !win.navigator.clipboard.writeText) throw Error("Clipboard unavailable");
        await win.navigator.clipboard.writeText(currentPlan.text);
        status.textContent="Checklist copied to clipboard.";
      } catch(e) {
        const fallbackText=host.querySelector("#et-path-copy-text");
        fallbackText.value=currentPlan.text;
        fallbackText.hidden=false;fallbackText.focus();fallbackText.select();
        status.textContent="Clipboard unavailable. The checklist is selected below for manual copy.";
      }
    });
    share.addEventListener("click",async()=>{
      const url=shareUrl(win.location.href,source.value,support.value).href;
      try {
        if (!win.navigator.clipboard || !win.navigator.clipboard.writeText) throw Error("Clipboard unavailable");
        await win.navigator.clipboard.writeText(url);
        status.textContent="Selection URL copied.";
      } catch(e) {
        const input=host.querySelector("#et-path-copy-text");
        input.value=url;input.hidden=false;input.focus();input.select();
        status.textContent="Copy the selected URL manually.";
      }
    });
    win.addEventListener("popstate",()=>{
      const state=validState(win.location.search);
      source.value=state.source; support.value=state.support;
      writePlan();
    });
    const state=validState(win.location.search);
    source.value=state.source;support.value=state.support;
    fallback.hidden=true;
    renderCatalog();writePlan();
  }
  return { catalog, filterCatalog, planFor, validState, shareUrl, init, PHASES, SUPPORT };
});
