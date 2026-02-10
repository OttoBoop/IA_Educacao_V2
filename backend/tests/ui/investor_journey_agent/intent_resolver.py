"""
Intent Resolver - Maps persona intent to working CSS selectors.

Bridges the gap between the persona LLM (which describes what it wants
to interact with) and the browser (which needs CSS selectors).
"""

from typing import List, Optional, Tuple

from .browser_interface import ClickableElement
from .llm_brain import Action, ActionType


class IntentResolver:
    """
    Resolves persona intent to a clickable element's CSS selector.

    Resolution strategy:
    1. If element_index is valid, use it to look up the selector directly
    2. If element_index is invalid/missing, fall back to fuzzy text matching
    3. If no match found, return None

    For click execution, provides execute_with_retry() which:
    1. Tries the resolved CSS selector
    2. Falls back to text-based Playwright selector
    3. Falls back to bounding box click as last resort
    """

    def resolve(
        self,
        action: Action,
        clickable_elements: List[ClickableElement],
    ) -> Optional[str]:
        """
        Resolve an action's intent to a CSS selector.

        Args:
            action: The LLM's action with element_index and/or target text
            clickable_elements: List of all clickable elements on the page

        Returns:
            CSS selector string, or None if no match found
        """
        if not clickable_elements:
            return None

        # Filter to visible elements only (matching what the LLM was shown)
        visible = [el for el in clickable_elements if el.occlusion_status == "visible"]
        if not visible:
            return None

        # Strategy 1: Index-based lookup (1-based)
        if action.element_index is not None:
            idx = action.element_index - 1  # Convert 1-based to 0-based
            if 0 <= idx < len(visible):
                return visible[idx].selector

        # Strategy 2: Fuzzy text matching against target
        target_text = action.target or action.intent_description or ""
        if target_text:
            return self._match_by_text(target_text, visible)

        return None

    def _match_by_text(
        self, target_text: str, elements: List[ClickableElement]
    ) -> Optional[str]:
        """Match target text against element text and aria_label."""
        target_lower = target_text.lower()

        # Pass 1: Exact match on text or aria_label
        for el in elements:
            if el.text and el.text.lower() == target_lower:
                return el.selector
            if el.aria_label and el.aria_label.lower() == target_lower:
                return el.selector

        # Pass 2: Substring match (target in element text)
        for el in elements:
            if el.text and target_lower in el.text.lower():
                return el.selector
            if el.aria_label and target_lower in el.aria_label.lower():
                return el.selector

        # Pass 3: Reverse substring (element text in target)
        for el in elements:
            if el.text and el.text.lower() in target_lower:
                return el.selector

        return None

    async def execute_with_retry(
        self,
        action: Action,
        clickable_elements: List[ClickableElement],
        browser,
    ) -> Optional[Tuple[bool, Optional[str]]]:
        """
        Execute a click action with silent retries using fallback strategies.

        Returns:
            (success, error_message) tuple for click actions
            None for non-click actions (caller should use default execution)
        """
        if action.action_type != ActionType.CLICK:
            return None  # Not our job — caller uses default execution

        # Resolve the selector
        selector = self.resolve(action, clickable_elements)

        # Get the matched element for fallback strategies
        matched_element = self._find_matched_element(action, clickable_elements)

        # Strategy 1: CSS selector click
        if selector:
            print(f"  [resolve] Trying CSS selector: {selector}")
            success = await browser.click(selector)
            if success:
                return True, None

        # Strategy 2: Text-based Playwright selector
        target_text = action.target or action.intent_description or ""
        if target_text:
            # Try Playwright's text selector
            text_selector = f"text={target_text}"
            print(f"  [resolve] Trying text selector: {text_selector}")
            try:
                success = await browser.click(text_selector)
                if success:
                    return True, None
            except Exception:
                pass

        # Strategy 3: Bounding box click as last resort
        if matched_element and matched_element.bounding_box:
            bbox = matched_element.bounding_box
            cx = bbox["x"] + bbox["width"] / 2
            cy = bbox["y"] + bbox["height"] / 2
            print(f"  [resolve] Trying bounding box click at ({cx:.0f}, {cy:.0f})")
            try:
                await browser.page.mouse.click(cx, cy)
                return True, None
            except Exception:
                pass

        # All strategies failed
        error_msg = f"Could not click '{target_text or selector}' after all retry strategies"
        return False, error_msg

    def _find_matched_element(
        self, action: Action, clickable_elements: List[ClickableElement]
    ) -> Optional[ClickableElement]:
        """Find the ClickableElement that matches the action's intent."""
        visible = [el for el in clickable_elements if el.occlusion_status == "visible"]
        if not visible:
            return None

        # By index
        if action.element_index is not None:
            idx = action.element_index - 1
            if 0 <= idx < len(visible):
                return visible[idx]

        # By text
        target_text = (action.target or action.intent_description or "").lower()
        if target_text:
            for el in visible:
                if el.text and target_text in el.text.lower():
                    return el
                if el.aria_label and target_text in el.aria_label.lower():
                    return el

        return visible[0] if visible else None
