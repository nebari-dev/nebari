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
      type: "doc",
      label: "Quickstart",
      id: "quickstart",
    },
    {
        type: 'category',
        label: 'Tutorials',
        link: {type: 'doc', id: 'tutorials/index'},
        items: [
          'tutorials/creating-cds-dashboard',
          "tutorials/using_dask",
        ],
    },
    {
      type: "category",
      label: "How-to Guides",
      link: {
        type: "generated-index",
        title: "How-to Guides",
        description:
          "Practical step-by-step guides to help you achieve a specific goal. Most useful when you're trying to get something done.",
        slug: "category/how-to",
        keywords: ["how-to"],
      },
      items: ["how-tos/overview"],
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
