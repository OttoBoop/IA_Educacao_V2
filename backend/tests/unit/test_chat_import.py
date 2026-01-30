#!/usr/bin/env python3
"""
Test script to check if chat_router can be imported
"""

try:
    from routes_chat import router as chat_router
    print("✅ Chat router imported successfully")
    print(f"Router has {len(chat_router.routes)} routes")
    for route in chat_router.routes[:5]:  # Show first 5 routes
        print(f"  - {route.methods} {route.path}")
except Exception as e:
    print(f"❌ Error importing chat_router: {e}")
    import traceback
    traceback.print_exc()