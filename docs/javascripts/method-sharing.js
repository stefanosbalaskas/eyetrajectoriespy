/* Bookmarkable method-selector choices. No telemetry or external requests. */
(function(factory){
  "use strict";
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(typeof document!=="undefined"){
    const init=()=>api.init(document,window);
    if(typeof document$!=="undefined"&&document$&&typeof document$.subscribe==="function")document$.subscribe(init);
    else if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);
    else init();
  }
})(function(){
  "use strict";
  const fields=[["et_grid","et-data"],["et_goal","et-goal"],["et_hierarchy","et-hierarchy"],["et_claim","et-uncertainty"]];
  function hydrate(params, allowed){
    const choices={};
    fields.forEach(([query,id])=>{
      const candidate=params.get(query);
      if(candidate!==null&&allowed[id].includes(candidate))choices[id]=candidate;
    });
    return choices;
  }
  function build(url,values){
    const next=new URL(url);
    fields.forEach(([query,id])=>next.searchParams.set(query,values[id]));
    return next;
  }
  function init(doc,win){
    const root=doc.getElementById("et-method");
    if(!root||root.dataset.shareReady)return;
    root.dataset.shareReady="1";
    const map=Object.fromEntries(fields.map(([,id])=>[id,root.querySelector("#"+id)]));
    const choices=Object.fromEntries(fields.map(([,id])=>[id,Array.from(map[id].options).map(o=>o.value)]));
    const field=root.querySelector("#et-share-link");
    const status=root.querySelector("#et-share-status");
    function current(){return Object.fromEntries(fields.map(([,id])=>[id,map[id].value]));}
    function updateUrl(){
      const next=build(win.location.href,current());
      field.value=next.href;
      win.history.replaceState(win.history.state,"",next.pathname+next.search+next.hash);
    }
    function restore(){
      const incoming=hydrate(new URL(win.location.href).searchParams,choices);
      Object.keys(incoming).forEach(id=>{map[id].value=incoming[id];});
      map["et-data"].dispatchEvent(new Event("change",{bubbles:true}));
      field.value=build(win.location.href,current()).href;
    }
    Object.values(map).forEach(el=>el.addEventListener("change",updateUrl));
    root.querySelector("#et-copy-link").addEventListener("click",async()=>{
      updateUrl();
      try{
        if(!win.navigator.clipboard||!win.navigator.clipboard.writeText)throw Error("Clipboard API unavailable");
        await win.navigator.clipboard.writeText(field.value);
        status.textContent="Selection URL copied.";
      }catch(e){field.focus();field.select();status.textContent="Copy the selected URL manually (Ctrl+C or Cmd+C).";}
    });
    win.addEventListener("popstate",restore);
    restore();
  }
  return {hydrate,build,init};
});
