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
url.

## Setup

Install Nebari with the development requirements (which include Playwright)

`pip install -e ".[dev]"`

The install playwright

`playwright install`


## Writing Playwright tests

In general most of the testing happens through `assertions` and `locators`.
The Playwright API has several mechanism for getting a locator for an item on
the page.

```python
button = self.page.get_by_role("button", name="Sign in with Keycloak")
```

Once you have a handle locator, you can interact with it in different ways,
depending on the type of object. For example, clicking
a button:

```python
button.click()
```

Occasionally you'll need to wait for things to load on the screen. We can
achieve this through several mechanisms. We can either wait for the page to
finish loading:

```python
self.page.wait_for_load_state("networkidle")
```

or we can wait for something specific to happen with the locator itself:

```python
button.wait_for(timeout=3000, state="attached")
```



## Notes
Playwright dev tips:
* when its running, don't touch anything - this should go without saying,
but its easy to forget
