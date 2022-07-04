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
        link: {
            type: 'doc', 
            id: 'tutorials/index'
        },
        items: [
          'tutorials/creating-cds-dashboard',
        ],
      },
    // {
    //     type: 'category',
    //     label: 'How-to Guides',
    //     link: {
    //         type: 'doc', 
    //         id: 'how-to/index'
    //     },
    //     items: [
    //     ],
    //   },
    // {
    //     type: 'category',
    //     label: 'Conceptual Guides',
    //     link: {
    //         type: 'doc', 
    //         id: 'explanations/index'
    //     },
    //     items: [
    //     ],
    //   },
    // {
    //     type: 'category',
    //     label: 'References',
    //     link: {
    //         type: 'doc', 
    //         id: 'reference/index'
    //     },
    //     items: [
    //     ],
    //   },
    {
      type: "doc",
      label: "Community",
      id: "governance/index",
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
