// Note: type annotations allow type checking and IDEs autocompletion
// @ts-check

// https://github.com/FormidableLabs/prism-react-renderer/tree/master/src/themes
const lightCodeTheme = require("prism-react-renderer/themes/nightOwlLight");
const darkCodeTheme = require("prism-react-renderer/themes/nightOwl");

// Adding reusable information
const githubOrgUrl = "https://github.com/nebari-dev";
const domain = "https://nebari.dev";

// -----------------------------------------------------------------------------
// custom Fields for the project
const customFields = {
  copyright: `Copyright © ${new Date().getFullYear()} | Made with 💜   by the Nebari dev team `,
  meta: {
    title: "Nebari",
    description: "An opinionated JupyterHub deployment for Data Science teams",
    keywords: ["Jupyter", "MLOps", "Kubernetes", "Python"],
  },
  domain,
  githubOrgUrl,
  githubUrl: `${githubOrgUrl}/nebari`,
  githubDocsUrl: `${githubOrgUrl}/nebari/tree/main/docs`,
};

// -----------------------------------------------------------------------------
// Main site config
/** @type {import('@docusaurus/types').Config} */
const config = {
  title: customFields.meta.title,
  tagline: customFields.meta.description,
  url: customFields.domain,
  baseUrl: "/",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  favicon: "img/favicon.ico",

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  // Plugings need installing first then add here
  plugins: [
    "docusaurus-plugin-sass",
    require.resolve('docusaurus-lunr-search'),
  ],
  customFields: { ...customFields },

  // ---------------------------------------------------------------------------
  // Edit presets
  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: "/",
          path: "docs",
          admonitions: {
            icons: "emoji",
          },
          sidebarPath: require.resolve("./sidebars.js"),
          sidebarCollapsible: true,
          // points to the Nebari repo
          // Remove this to remove the "edit this page" links.
          editUrl: customFields.githubDocsUrl,
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/scss/application.scss"),
        },
      }),
    ],
  ],

  // ---------------------------------------------------------------------------
  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      docs: {
        sidebar: {
          autoCollapseCategories: true,
          hideable: true,
        },
      },
      navbar: {
        title: customFields.meta.title,
        // TODO: Replace with logo
        // logo: {
        //   alt: "Nebari logo - Docs home",
        //   src: "img/logo.svg",
        // },
        style: "dark",
        hideOnScroll: true,
        items: [
          {
            label: "Getting Started",
            position: "right",
            to: "getting-started/installing-nebari",
          },
          {
            label: "Tutorials",
            position: "right",
            to: "tutorials",
          },
          {
            label: "How-to Guides",
            position: "right",
            to: "how-tos",
          },
          {
            label: "Reference",
            position: "right",
            to: "references/overview",
          },
          {
            label: "Conceptual Guides",
            position: "right",
            to: "explanations/overview",
          },
          {
            label: "Community",
            position: "right",
            to: "governance/overview",
          },
          {
            href: customFields.githubUrl,
            position: "right",
            className: "header-github-link",
            "aria-label": "GitHub repository",
          },
        ],
      },
      footer: {
        copyright: customFields.copyright,
        style: "dark",
        links: [
          {
            title: "Open source",
            items: [
              {
                label: "Getting Started",
                to: "getting-started/installing-nebari",
              },
            ],
          },
          {
            title: "Community",
            items: [
              {
                label: "Nebari repository",
                href: customFields.githubUrl,
              },
            ],
          },
          {
            title: "Other",
            items: [
              {
                html: `
                <a href="https://www.netlify.com" target="_blank" rel="noreferrer noopener" aria-label="Deploys by Netlify">
                  <img src="https://www.netlify.com/img/global/badges/netlify-color-accent.svg" alt="Deploys by Netlify" width="114" height="51" />
                </a>
              `,
              },
            ],
          },
        ],
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
