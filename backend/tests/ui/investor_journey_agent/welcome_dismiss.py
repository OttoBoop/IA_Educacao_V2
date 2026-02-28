"""
Setup script: Dismiss the welcome overlay before the journey step loop.
Used with: --setup welcome_dismiss.py

Clicks the "Começar a Usar →" button on the welcome modal.
The script receives `page` and `browser` in its local namespace via exec().
"""
import asyncio


async def _dismiss():
    await page.wait_for_load_state("networkidle", timeout=15000)

    # Try to close the welcome modal if it appears
    await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
    await asyncio.sleep(0.5)

    print("[Setup] Welcome modal dismissed")


asyncio.get_event_loop().run_until_complete(_dismiss())
