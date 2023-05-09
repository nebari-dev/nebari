# Nebari integration testing with Playwright


## How does it work?

Playwright manages interactions with any website. We are using it to interact
with a deployed Nebari instance and test the various integrations that are
included.

For our test suite, we utilize Playwright's synchronous API. The first task
is to launch the web browser you'd like to test in. Options in our test suite
are `chromium`, `webkit`, and `firefox`. Playwright uses browser contexts to
achieve test isolation. The context can either be created by default or
manually (for the purposes of generating multiple contexts per test in the case
of admin vs user testing). Next the page on the browser is created. For all
tests this starts as a blank page, then during the test, we navigate to a given
url. This is all achieved in the `setup` method of the `Navigator` class.

## Setup

Install Nebari with the development requirements (which include Playwright)

`pip install -e ".[dev]"`

Then install playwright itself (rerquired).

`playwright install`

:::note
If you see the warning `BEWARE: your OS is not officially supported by Playwright; downloading fallback build.`, it is not critical. Playwright will likely still
work https://github.com/microsoft/playwright/issues/15124

## Writing Playwright tests

In general most of the testing happens through `locators` which is Playwright's
way of connecting a python object to the HTML element on the page.
The Playwright API has several mechanisms for getting a locator for an item on
the page (`get_by_role`, `get_by_text`, `get_by_label`, `get_by_placeholder`,
etc).

```python
button = self.page.get_by_role("button", name="Sign in with Keycloak")
```

Once you have a handle on a locator, you can interact with it in different ways,
depending on the type of object. For example, clicking
a button:

```python
button.click()
```

Occasionally you'll need to wait for things to load on the screen. We can
either wait for the page to finish loading:

```python
self.page.wait_for_load_state("networkidle")
```

or we can wait for something specific to happen with the locator itself:

```python
button.wait_for(timeout=3000, state="attached")
```

Note that waiting for the page to finish loading may be deceptive inside of
Jupyterlab since things may need to load _inside_ the page, not necessarily
causing network traffic - or causing several bursts network traffic, which
would incorrectly pass the `wait_for_load_state` after the first burst.
