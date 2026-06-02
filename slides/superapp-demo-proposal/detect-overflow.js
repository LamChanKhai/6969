module.paths.push('/usr/lib/node_modules');
process.env.PLAYWRIGHT_BROWSERS_PATH = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/playwright-browsers';
const path=require('path');
const {chromium}=require('playwright');
(async()=>{
  const b=await chromium.launch({headless:true});
  const ctx=await b.newContext({viewport:{width:1920,height:1080}});
  const p=await ctx.newPage();
  await p.goto('file://'+path.join(__dirname,'deck.html'),{waitUntil:'networkidle'});
  await p.evaluate(()=>document.fonts.ready);
  // Hide chrome, unwrap slides, force reflow before measuring.
  // Only target slides inside .deck (not thumbnail clones in .thumb-nav).
  await p.addStyleTag({content:`
    #slide-nav,.theme-toggle,.thumb-toggle,.thumb-nav{display:none!important}
    html,body{padding-top:0!important;padding-left:0!important}
    .slide-wrap{width:1920px!important;height:auto!important;overflow:visible!important}
    .slide-wrap > .slide{transform:none!important}
    .slide{width:1920px!important;height:auto!important;min-height:0!important;max-height:none!important;overflow:visible!important}
  `});
  // Force a full reflow so the browser recalculates heights
  await p.evaluate(() => {
    void document.documentElement.offsetHeight;
    return new Promise(r => requestAnimationFrame(r));
  });
  await new Promise(r => setTimeout(r, 300));
  const SUFFIXES = /^(万|億|円|%|$|USD|JPY|VND|KB|MB|GB|TB|kg|cm|mm|m|km|s|ms|μs|ns|h|min|d|w|mo|y|円?\/月|\/年)$/;
  const r = await p.evaluate(() => {
    // Only measure slides that are direct children of .slide-wrap inside .deck
    return Array.from(document.querySelectorAll('.deck > .slide-wrap > .slide')).map((s, i) => {
      const head = (s.querySelector("h1,h2") || {}).textContent?.trim().slice(0, 40) || "";
      const breaks = [];
      for (const el of s.querySelectorAll("h1,h2,h3,.big-number,.card-title")) {
        const txt = (el.textContent || "").trim();
        if (!txt || txt.length < 2) continue;
        const rects = el.getClientRects();
        if (rects.length < 2) continue;
        const lastW = rects[rects.length - 1].width;
        const firstW = rects[0].width;
        if (lastW > firstW * 0.5) continue;
        const tail = txt.slice(-4).trim();
        const SUFFIXES = /^(万|億|円|%|$|USD|JPY|VND|KB|MB|GB|TB|kg|cm|mm|m|km|s|ms|μs|ns|h|min|d|w|mo|y|円?\/月|\/年)$/;
        if (lastW < firstW * 0.25 || (lastW < 120 && SUFFIXES.test(tail))) {
          breaks.push(`${el.tagName.toLowerCase()}:${JSON.stringify(tail)}`);
        }
      }
      return { idx: i + 1, id: s.id, h: s.scrollHeight, head, breaks };
    });
  });
  await b.close();
  const over = r.filter(x => x.h > 1080);
  const under = r.filter(x => x.h < 650 && !(x.cls || "").match(/cover|section-divider/));
  const wrapped = r.filter(x => x.breaks.length > 0);
  console.log(`\n=== ${over.length}/${r.length} slides overflow 1080px ===`);
  over.forEach(x => console.log(`  #${String(x.idx).padStart(2, "0")}  ${x.h}px  ${x.head}`));
  console.log(`\n=== ${under.length}/${r.length} slides under-fill (<650px) -- bump density modifier ===`);
  under.forEach(x => console.log(`  #${String(x.idx).padStart(2, "0")}  ${x.h}px  ${x.head}`));
  console.log(`\n=== ${wrapped.length}/${r.length} slides with awkward word-breaks (last line short / unit-only) ===`);
  wrapped.forEach(x => console.log(`  #${String(x.idx).padStart(2, "0")}  ${x.head}  -- ${x.breaks.join(", ")}`));
  process.exit(over.length + under.length + wrapped.length ? 1 : 0);
})();
