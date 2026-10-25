"use strict";
const assert=require("node:assert/strict");
const {catalog,filterCatalog,planFor,validState,shareUrl,PHASES,SUPPORT}=require("../docs/javascripts/integration-navigator.js");
const fs=require("node:fs");
const path=require("node:path");
const SITE="https://stefanosbalaskas.github.io/eyetrajectoriespy/integrations/navigator/";
function assertDocumentTarget(href,label){
  const target=new URL(href,SITE);
  assert.equal(target.origin,"https://stefanosbalaskas.github.io",label);
  const route=target.pathname.replace(/^\/eyetrajectoriespy\//,"").replace(/\/$/,"");
  const file=path.join(__dirname,"..","docs",route+".md");
  assert.ok(fs.existsSync(file),label+" points to missing documentation "+route);
}
const rows=catalog();
assert.equal(rows.length,14);
assert.equal(new Set(rows.map(x=>x.id)).size,rows.length);
assert.equal(filterCatalog("", "all", "all").length,14);
assert.equal(filterCatalog("eye", "acquisition", "preview").length,2);
assert.ok(filterCatalog("eye", "acquisition", "preview").some(item=>item.id==="syelink"));
assert.equal(filterCatalog("Neon", "acquisition", "planned")[0].id,"pyneon");
assert.equal(filterCatalog("zz-nothing-ever","all","all").length,0);
assert.equal(filterCatalog("","functional","optional").length,3);
for(const row of rows){
  assert.ok(PHASES[row.phase]);
  assert.ok(["tables","acquisition","standards","functional","companion"].includes(row.group));
  assert.match(row.guide,/^\.\.\/(?:\.\.\/)?/);
  const target=new URL(row.guide,"https://stefanosbalaskas.github.io/eyetrajectoriespy/integrations/navigator/");
  assert.equal(target.origin,"https://stefanosbalaskas.github.io");
  assert.ok(target.pathname.startsWith("/eyetrajectoriespy/"));
  assert.match(row.upstream,/^https:\/\//);
  assertDocumentTarget(row.guide, row.name);
  assert.ok(row.boundary.length>15);
}
const ids=["table","pymovements","syelink","bids","pyneon","eye2bids","eyelinkio","pyelink","pandera","eyekit","pupeyes","scikit-fda","fdapy","fdasrsf"];
assert.deepEqual(rows.map(x=>x.id),ids);
for(const id of ids){
  for(const support of Object.keys(SUPPORT)){
    const plan=planFor(id,support);
    assert.equal(plan.source,id);
    assert.equal(plan.steps.length,5);
    assert.match(plan.text,/No file was processed or validated/);
    assert.match(plan.text,/participant ID/);
    assert.match(plan.text,/upstream/);
    assert.match(plan.text,/scientifically valid inference/);
    assert.ok(plan.supportGuide.startsWith("../"));
    assertDocumentTarget(plan.supportGuide,id+"/"+support);
  }
}
assert.match(planFor("syelink","aligned").boundary,/real EyeLink ASC accuracy not qualified/);
assert.match(planFor("bids","unknown").boundary,/not official BIDS conformance/);
assert.match(planFor("pymovements","async").steps.join(" "),/coordinate-specific clocks/);
assert.match(planFor("table","repeated").steps.join(" "),/participant clusters/);
const defaultState=validState("?et_source=../../evil&et_support=untrusted");
assert.deepEqual(defaultState,{source:"table",support:"unknown"});
assert.deepEqual(validState("?et_source=syelink&et_support=sparse"),{source:"syelink",support:"sparse"});
const url=shareUrl("https://stefanosbalaskas.github.io/eyetrajectoriespy/integrations/navigator/?keep=yes#plan","syelink","sparse");
assert.equal(url.hash,"#plan");
assert.equal(url.searchParams.get("keep"),"yes");
assert.equal(url.searchParams.get("et_source"),"syelink");
assert.equal(url.searchParams.get("et_support"),"sparse");
console.log("PASS integration navigator source, filters, disclaimer, shareable state and path contracts");
