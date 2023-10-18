import pytest
from playwright.sync_api import Page, expect


@pytest.mark.local
def test_login(page: Page, local_test_credential):
    _, _, domain = local_test_credential
    page.goto(f"https://{domain}")
    # page.goto("https://nebari.quansight.dev/")

    page.screenshot(path="screenshots/homepage.png")
    locator = page.locator("#login-main > div > a")
    expect(locator).to_be_visible()
    locator.click()

    page.screenshot(path="screenshots/login.png")
    locator = page.locator("#social-auth0")
    expect(locator).to_be_visible()
    locator.click()

    page.screenshot(path="screenshots/auth0.png")
    expect(page.get_by_placeholder("yours@example.com")).to_be_visible()


@pytest.mark.local
def test_password_login(page: Page, local_test_credential):
    username, password, domain = local_test_credential
    page.goto(f"https://{domain}")
    page.locator("#login-main > div > a").click()
    page.locator("#username").fill(username)
    page.locator("#password").fill(password)
    page.locator("#kc-login").click()
    page.screenshot(path="screenshots/password_login.png")
