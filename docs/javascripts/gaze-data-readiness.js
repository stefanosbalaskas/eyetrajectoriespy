/* Local-only structural inspector. Never sends gaze data to a server. */
(function(factory){
  "use strict";
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(typeof document!=="undefined"){
    const init=()=>api.init(document);
    if(typeof document$!=="undefined"&&document$&&typeof document$.subscribe==="function")document$.subscribe(init);
    else if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);
    else init();
  }
})(function(){
  "use strict";
  const needed=["participant_id","trial_id","time_s","x","y"];
  function parseCsv(source){
    if(typeof source!=="string"||!source.trim())throw Error("Provide nonempty CSV.");
    if(source.length>1200000)throw Error("Local CSV exceeds 1.2 million characters.");
    const s=source.replace(/^\uFEFF/,""), records=[];
    let row=[],cell="",quoted=false,closed=false;
    function endCell(){row.push(cell);cell="";closed=false;}
    function endRow(){
      endCell();
      if(!(row.length===1&&!row[0].trim()))records.push(row);
      row=[];
      if(records.length>12001)throw Error("CSV exceeds 12,000 data rows.");
    }
    for(let i=0;i<s.length;i++){
      const ch=s[i];
      if(quoted){
        if(ch==='"'){if(s[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}
        else cell+=ch;
      }else if(ch==='"'&&!cell&&!closed)quoted=true;
      else if(ch===",")endCell();
      else if(ch==="\n"||ch==="\r"){if(ch==="\r"&&s[i+1]==="\n")i++;endRow();}
      else if(ch==='"')throw Error("Unescaped quotation mark.");
      else if(closed&&!/\s/.test(ch))throw Error("Characters after closing CSV quotation.");
      else if(!closed)cell+=ch;
    }
    if(quoted)throw Error("Unterminated CSV quotation.");
    if(row.length||cell)endRow();
    if(records.length<2)throw Error("CSV requires a header and at least one row.");
    const headers=records.shift().map(x=>x.trim());
    if(headers.some(x=>!x)||new Set(headers).size!==headers.length)throw Error("Missing or duplicate column headers.");
    records.forEach((r,i)=>{if(r.length!==headers.length)throw Error("Row "+(i+2)+" has "+r.length+" cells; expected "+headers.length+".");});
    return {headers,rows:records};
  }
  function inspect(parsed,opts={}){
    const missing=needed.filter(x=>!parsed.headers.includes(x));
    if(missing.length)throw Error("Required columns missing: "+missing.join(", "));
    const ix=Object.fromEntries(parsed.headers.map((h,i)=>[h,i]));
    const units=new Map(),participants=new Set(),flags=[];
    let badId=0,badTime=0,badXY=0,missingXY=0,missingBoth=0,uniqueChannels=0,paired=0,duplicates=0,unordered=0,outside=0;
    const coord=opts.coordinateSystem||"undeclared", timeUnit=opts.timeUnit||"undeclared";
    for(const row of parsed.rows){
      const p=row[ix.participant_id].trim(),trial=row[ix.trial_id].trim();
      if(!p||!trial){badId++;continue;}
      participants.add(p);
      const key=JSON.stringify([p,trial]);
      if(!units.has(key))units.set(key,{times:[],seen:new Set(),last:null});
      const unit=units.get(key),raw=row[ix.time_s].trim(),t=raw===""?NaN:Number(raw);
      if(!Number.isFinite(t)){badTime++;continue;}
      if(unit.seen.has(t))duplicates++;
      unit.seen.add(t);
      if(unit.last!==null&&t<=unit.last)unordered++;
      unit.last=t;unit.times.push(t);
      const xr=row[ix.x].trim(),yr=row[ix.y].trim(),xm=xr==="",ym=yr==="";
      if(xm||ym)missingXY++;
      if(xm&&ym)missingBoth++;
      if(xm!==ym)uniqueChannels++;
      if(!xm&&!ym)paired++;
      const x=xm?NaN:Number(xr),y=ym?NaN:Number(yr);
      if((!xm&&!Number.isFinite(x))||(!ym&&!Number.isFinite(y)))badXY++;
      if(coord==="normalized"&&((Number.isFinite(x)&&(x<0||x>1))||(Number.isFinite(y)&&(y<0||y>1))))outside++;
    }
    const grouped=Array.from(units.values()),first=grouped.length?grouped[0].times:[];
    const aligned=Boolean(grouped.length)&&grouped.every(g=>g.times.length===first.length&&g.times.every((t,i)=>t===first[i]));
    const repeated=units.size>participants.size;
    if(badId)flags.push(badId+" rows lack participant or trial identity.");
    if(badTime)flags.push(badTime+" rows have missing/nonfinite time.");
    if(badXY)flags.push(badXY+" rows have nonfinite observed coordinate values.");
    if(duplicates)flags.push(duplicates+" duplicate within-trial timestamps.");
    if(unordered)flags.push(unordered+" nonincreasing adjacent timestamps.");
    if(missingXY)flags.push(missingXY+" rows have missing coordinates; do not replace with zero.");
    if(missingBoth)flags.push(missingBoth+" rows have neither coordinate.");
    if(outside)flags.push(outside+" rows outside declared normalized [0,1] coordinates.");
    if(repeated)flags.push("Repeated trials within participants: do not treat trials as independent people.");
    if(timeUnit==="undeclared"||coord==="undeclared")flags.push("Time or coordinate units undeclared; no conversions performed.");
    let suggestion;
    if(badId||badTime||badXY||duplicates||unordered)suggestion="Resolve structural inconsistencies before model selection.";
    else if(!missingXY&&aligned)suggestion="Common-grid paired x/y candidate; evaluate dense functional methods and independent units.";
    else if(!missingXY)suggestion="Paired native x/y candidate on unequal time grids; inspect sparse methods.";
    else if(uniqueChannels)suggestion="Coordinate-specific samples appear: verify acquisition semantics before asynchronous analysis.";
    else suggestion="Partially missing paired samples; establish observation mechanism before modelling.";
    return {
      status:flags.length?"Review required":"No issues detected by these limited structural checks",
      rows:parsed.rows.length,participants:participants.size,curves:units.size,
      commonGrid:aligned,repeatedTrials:repeated,pairedRows:paired,
      missingCoordinateRows:missingXY,missingBothRows:missingBoth,coordinateSpecificRows:uniqueChannels,
      invalidTimeRows:badTime,invalidCoordinateRows:badXY,invalidIdentityRows:badId,
      duplicateWithinTrialTimes:duplicates,nonincreasingTimes:unordered,
      outsideDeclaredNormalizedRows:outside,declaredTimeUnit:timeUnit,declaredCoordinateSystem:coord,
      suggestedReading:suggestion,flags,
      scope:"Structural diagnostics only; no sensor QC, imputation, mechanism identification, modelling or calibrated inference."
    };
  }
  function init(doc){
    const root=doc.getElementById("et-data-audit");
    if(!root||root.dataset.ready)return;
    root.dataset.ready="1";
    const form=root.querySelector("form"),file=root.querySelector("#et-csv-file"),
      paste=root.querySelector("#et-csv-paste"),message=root.querySelector("#et-audit-status"),
      report=root.querySelector("#et-audit-report"),exportButton=root.querySelector("#et-export-audit");
    let last=null;
    function clear(){report.replaceChildren();last=null;exportButton.disabled=true;}
    function line(label,value){
      const p=doc.createElement("p"),b=doc.createElement("strong");
      b.textContent=label+": ";p.append(b,doc.createTextNode(String(value)));report.appendChild(p);
    }
    root.querySelector("#et-use-sample").addEventListener("click",()=>{
      file.value="";paste.value=[
        "participant_id,trial_id,time_s,x,y,condition",
        "P01,T1,0,0.1,0.3,A","P01,T1,0.1,0.2,0.36,A",
        "P02,T1,0,0.4,0.3,B","P02,T1,0.1,0.44,0.39,B",
        "P03,T1,0,0.2,0.6,A","P03,T1,0.1,0.25,0.58,A"
      ].join("\n");clear();message.textContent="Invented example loaded; select Inspect CSV.";
    });
    file.addEventListener("change",()=>{if(file.files.length)paste.value="";clear();message.textContent="File selected for local inspection. Nothing is uploaded.";});
    form.addEventListener("submit",async event=>{
      event.preventDefault();clear();
      try{
        const f=file.files&&file.files[0];
        if(f&&f.size>3000000)throw Error("Local file exceeds the permitted size.");
        const parsed=parseCsv(f?await f.text():paste.value);
        const result=inspect(parsed,{
          timeUnit:root.querySelector("#et-time-unit").value,
          coordinateSystem:root.querySelector("#et-coordinate-unit").value
        });
        last=result;exportButton.disabled=false;
        line("Status",result.status);
        line("Rows / participants / curves",result.rows+" / "+result.participants+" / "+result.curves);
        line("Time grid",result.commonGrid?"Identical recorded timestamps across curves":"Unequal recorded support");
        line("Paired rows / rows with missing x or y",result.pairedRows+" / "+result.missingCoordinateRows);
        line("Starting point",result.suggestedReading);
        const h=doc.createElement("h3");h.textContent="Review items";report.appendChild(h);
        const ul=doc.createElement("ul");
        (result.flags.length?result.flags:["No checked anomalies; this is not statistical validation."]).forEach(x=>{
          const li=doc.createElement("li");li.textContent=x;ul.appendChild(li);
        });report.appendChild(ul);
        line("Scientific boundary",result.scope);
        message.textContent="Local inspection completed; only summary counts are displayed.";
      }catch(e){message.textContent="Cannot inspect CSV: "+e.message;}
    });
    exportButton.addEventListener("click",()=>{
      if(!last)return;
      const url=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)+"\n"],{type:"application/json"}));
      const a=doc.createElement("a");a.href=url;a.download="eyetrajectoriespy-structure-audit.json";doc.body.appendChild(a);
      a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
  }
  return {parseCsv,inspect,init};
});
