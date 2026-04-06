"""In-page captcha detection via DOM analysis."""
from __future__ import annotations

from captcha_solver.browser.base import BrowserAdapter, CaptchaElementInfo

# Known captcha selectors
CAPTCHA_SIGNATURES = [
    {
        "type": "recaptcha_v2",
        "selectors": [
            "iframe[src*='recaptcha']",
            "div.g-recaptcha",
            "#g-recaptcha-response",
        ],
        "site_key_attr": "data-sitekey",
        "site_key_selector": "div.g-recaptcha",
    },
    {
        "type": "hcaptcha",
        "selectors": ["iframe[src*='hcaptcha']", "div.h-captcha"],
        "site_key_attr": "data-sitekey",
        "site_key_selector": "div.h-captcha",
    },
    {
        "type": "turnstile",
        "selectors": [
            "iframe[src*='challenges.cloudflare.com']",
            "div.cf-turnstile",
        ],
        "site_key_attr": "data-sitekey",
        "site_key_selector": "div.cf-turnstile",
    },
    {
        "type": "geetest",
        "selectors": ["div.geetest_holder", "div.geetest_panel", ".geetest_btn"],
        "site_key_attr": "",
        "site_key_selector": "",
    },
    {
        "type": "text",
        "selectors": [
            "img[src*='captcha']",
            "img.captcha",
            "#captcha-image",
            "img[alt*='captcha']",
        ],
        "site_key_attr": "",
        "site_key_selector": "",
    },
]


def detect_captcha_in_page(adapter: BrowserAdapter) -> CaptchaElementInfo | None:
    """Scan the page DOM for known captcha elements."""
    for sig in CAPTCHA_SIGNATURES:
        for selector in sig["selectors"]:
            try:
                elements = adapter.find_elements(selector)
                if elements:
                    element = elements[0]
                    site_key = ""
                    if sig["site_key_selector"]:
                        try:
                            sk_el = adapter.find_element(sig["site_key_selector"])
                            site_key = (
                                adapter.get_element_attribute(sk_el, sig["site_key_attr"]) or ""
                            )
                        except Exception:
                            pass

                    return CaptchaElementInfo(
                        captcha_type=sig["type"],
                        element=element,
                        site_key=site_key,
                        page_url=adapter.get_page_url(),
                        needs_interaction=sig["type"] not in ("text",),
                    )
            except Exception:
                continue
    return None
