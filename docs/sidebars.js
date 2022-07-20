/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */

module.exports = {
  sidebar: [
    {
      type: "doc",
      label: "Introduction",
      id: "welcome",
    },
    {
      type: "category",
      label: "Getting Started",
      link: {
        type: "generated-index",
        title: "Getting Started",
        description:
          "This section describes how to install and deploy Nebari on a selection of cloud providers, and provides details on how Nebari can be configured and customized to fit a variety of deployment requirements.",
        slug: "category/getting-started",
        keywords: ["getting-started"],
      },
      items: [
        "getting-started/installing-nebari",
        "getting-started/deploy",
        "getting-started/cloud-providers",
      ],
    },
    {
      type: "category",
      label: "Tutorials",
      link: { type: "doc", id: "tutorials/index" },
      items: [
        "tutorials/creating-cds-dashboard",
        "tutorials/cost-estimate-report",
        "tutorials/creating-new-environments",
      ],
    },
    {
      type: "category",
      label: "How-to Guides",
      link: { type: "doc", id: "how-tos/index" },
      items: [
        "how-tos/kbatch-howto",
        "how-tos/nebari-gcp",
        "how-tos/nebari-aws",
        "how-tos/nebari-do",
        "how-tos/nebari-azure",
        "how-tos/nebari-hpc",
        "how-tos/domain-registry",
        "how-tos/login-keycloak",
        "how-tos/configuring-keycloak",
      ],
    },
    {
      type: "category",
      label: "Conceptual Guides",
      link: {
        type: "generated-index",
        title: "Conceptual Guides",
        description:
          "Big-picture explanations of higher-level Nebari concepts. Most useful for building understanding of a particular topic.",
        slug: "category/conceptual-guides",
        keywords: ["conceptual-guides"],
      },
      items: ["explanations/overview"],
    },
    {
      type: "category",
      label: "Reference",
      link: {
        type: "generated-index",
        title: "Reference Guides",
        description:
          "Nitty-gritty technical descriptions of how Nebari works. ",
        slug: "category/reference",
        keywords: ["reference"],
      },
      items: ["references/overview"],
    },
    {
      type: "doc",
      label: "Community",
      id: "governance/overview",
    },
    {
      type: "doc",
      label: "FAQs / Troubleshooting",
      id: "troubleshooting",
    },
    {
      type: "doc",
      label: "Glossary",
      id: "glossary",
    },
  ],
};
