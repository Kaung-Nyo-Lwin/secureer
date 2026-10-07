"""Run against a local server; optionally install Playwright to reproduce."""

import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE_URL = os.environ.get("SECUREER_URL", "http://127.0.0.1:8000")
SCREENSHOTS = Path(__file__).resolve().parent.parent / "docs" / "images"


def assert_no_overflow(page):
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), (
        f"Horizontal overflow at {page.viewport_size} on {page.url}"
    )


def complete_profile(page, keyboard=False):
    page.get_by_label("First name").fill("Browser test")
    page.get_by_label("Current or recent role").fill("Marketing Manager")
    page.get_by_role("textbox", name="Your skills").fill(
        "Digital marketing, Market Research, Content writing skills, Communication Skills"
    )
    submit = page.get_by_role("button", name="Explore my career")
    if keyboard:
        submit.press("Enter")
    else:
        submit.click()
    page.wait_for_url("**/result/*/")
    expect(page.get_by_role("heading", name="Automation exposure")).to_be_visible()
    expect(page.get_by_text("Digital marketing", exact=True).first).to_be_visible()
    expect(page.locator(".career")).to_have_count(5)


def main():
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1080})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: (
                errors.append(message.text) if message.type == "error" else None
            ),
        )

        assert page.goto(BASE_URL).status == 200
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Skip to content")).to_be_focused()
        page.keyboard.press("Escape")
        page.locator("body").click(position={"x": 1, "y": 200})
        assert_no_overflow(page)
        page.screenshot(path=str(SCREENSHOTS / "home-desktop.png"), full_page=True)
        page.get_by_role("button", name="+ Leadership", exact=True).click()
        expect(page.get_by_role("textbox", name="Your skills")).to_have_value(
            "Leadership"
        )
        page.get_by_role("button", name="✓ Leadership", exact=True).click()
        expect(page.get_by_role("textbox", name="Your skills")).to_have_value("")
        complete_profile(page)
        report_url = page.url
        page.locator(".career summary").first.click()
        expect(page.locator(".career-detail").first).to_be_visible()
        page.go_back()
        expect(page.get_by_role("button", name="Explore my career")).to_be_enabled()
        page.goto(report_url)
        page.get_by_role("button", name="Delete this report").click()
        page.wait_for_url(BASE_URL + "/")

        for width in [320, 390, 768, 1440]:
            page.set_viewport_size(
                {"width": width, "height": 1080 if width == 1440 else 844}
            )
            for path in ["/", "/example/", "/about/"]:
                response = page.goto(BASE_URL + path)
                assert response.status == 200
                assert_no_overflow(page)
                if path == "/" and width == 390:
                    page.screenshot(
                        path=str(SCREENSHOTS / "home-mobile.png"), full_page=True
                    )
                if path == "/example/" and width == 1440:
                    page.screenshot(
                        path=str(SCREENSHOTS / "report-desktop.png"), full_page=True
                    )

        no_js = browser.new_context(
            java_script_enabled=False, viewport={"width": 390, "height": 844}
        )
        plain_page = no_js.new_page()
        plain_page.goto(BASE_URL)
        complete_profile(plain_page, keyboard=True)
        assert_no_overflow(plain_page)
        plain_page.get_by_role("button", name="Delete this report").press("Enter")
        plain_page.wait_for_url(BASE_URL + "/")
        no_js.close()
        assert not errors, errors
        browser.close()
        print(
            "Browser checks passed: desktop/mobile, profile submission, suggestions, details, deletion, back navigation, and no-JavaScript flow."
        )


if __name__ == "__main__":
    main()
