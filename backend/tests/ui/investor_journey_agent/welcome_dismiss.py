"""
Setup script: Dismiss the welcome overlay before the journey step loop.
Used with: --setup welcome_dismiss.py

Uses nest_asyncio to allow running async Playwright calls inside the
already-running event loop.
"""
import asyncio
import nest_asyncio

nest_asyncio.apply()


async def _dismiss():
    await page.wait_for_load_state("networkidle", timeout=15000)
    await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
    await asyncio.sleep(0.5)
    print("[Setup] Welcome modal dismissed")


asyncio.get_event_loop().run_until_complete(_dismiss())
