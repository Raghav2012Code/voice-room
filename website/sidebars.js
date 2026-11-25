// @ts-check
/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    'intro',
    'quickstart',
    {
      type: 'category',
      label: 'Engines',
      collapsed: false,
      items: ['engines/overview', 'engines/adding-an-engine'],
    },
    {
      type: 'category',
      label: 'Using Voice Room',
      collapsed: false,
      items: ['configuration', 'desktop-app', 'api'],
    },
    'troubleshooting',
    'faq',
  ],
};

module.exports = sidebars;
