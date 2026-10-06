import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1968,'height':1200})
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('file:///home/claude/egel/index.html'); await pg.wait_for_timeout(4000)
        await pg.add_style_tag(content='#player{max-width:1920px!important}'); await pg.evaluate('fit()')
        n=await pg.evaluate('scenes.length')
        for k in range(n):
            d=await pg.evaluate(f'DUR[{k}]'); T=d-0.6
            await pg.evaluate(f'''()=>{{pause(); go({k},true); t={T}; document.getAnimations().forEach(a=>{{ if(a.effect&&a.effect.target&&a.effect.target.id==='wipe') a.finish(); else a.currentTime={T*1000}; }}); cc.textContent=cueAt({k},{T}); }}''')
            await pg.wait_for_timeout(180)
            await (await pg.query_selector('#viewport')).screenshot(path=f'shots/s{k:02d}.png')
        print('errors', errs)
        await b.close()
asyncio.run(main())
