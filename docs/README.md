# Website

This website is built using [Docusaurus 2](https://docusaurus.io/), a modern static website generator.

- [Website](#website)
  - [Prerequisites](#prerequisites)
  - [Documentation local Development](#documentation-local-development)
  - [Build](#build)
  - [Adding a New Dependency](#adding-a-new-dependency)
  - [Deployment](#deployment)
  - [Linting](#linting)

## Prerequisites

To build the site you will need to have Node.js installed. To see if you already have Node.js installed, type the following command into your local command line terminal:

```console
$ node -v
v14.17.0
```

If you see a version number, such as `v14.17.0` printed, you have Node.js installed. If you get a `command not found` error (or similar phrasing), please install Node.js before continuing.

To install node visit [nodejs.org](https://nodejs.org/en/download/) or check any of these handy tutorials for [Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-node-js-on-ubuntu-20-04), [Debian](https://www.digitalocean.com/community/tutorials/how-to-install-node-js-on-debian-10), or [macOS](https://www.digitalocean.com/community/tutorials/how-to-install-node-js-and-create-a-local-development-environment-on-macos).

Once you have Node.js installed you can proceed to install Yarn. Yarn has a unique way of installing and running itself in your JavaScript projects. First you install the yarn command globally, then you use the global yarn command to install a specific local version of Yarn into your project directory.

The Yarn maintainers recommend installing Yarn globally by using the `NPM` package manager, which is included by default with all Node.js installations.
Use the `-g` flag with `npm` install to do this:

```bash
npm install -g yarn
```

After the package installs, have the yarn command print its own version number. This will let you verify it was installed properly:

```console
$ yarn --version
1.22.11
```

## Local development

1. First make sure to be in the `/docs` directory:

   ```bash
   cd docs
   ```

2. Install the necessary dependencies:

   ```bash
   yarn install
   ```

3. Then run the following command to start the development server:

   ```bash
   yarn start
   ```

   This command starts a local development server and opens up a browser window.
   Most changes are reflected live without having to restart the server.

> **Note**
> By default, this will load your site at <http://localhost:3000/>.

## Building the site

To build the static files of your website for production, run:

```bash
yarn build
```

This command generates static content into the `docs/build` directory and can be served using any static contents hosting service.
You can check the new build site with the following command:

```bash
yarn run serve
```

> **Note**
> By default, this will load your site at <http://localhost:3000/>.

## Adding a New Dependency

Use the `add` subcommand to add new dependencies:

```bash
yarn add package-name
```

## Deployment

The deployment is automatically handled by Netlify when content is merged into the `main` branch.

## Linting

Before opening a PR, run the docs linter and formatter to ensure code consistency. From the `docs` directory, run:

```bash
yarn run lint
yarn run format
```
