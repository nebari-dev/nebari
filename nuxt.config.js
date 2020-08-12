const routerBase = process.env.DEPLOY_ENV === 'GH_PAGES' ? {
  router: {
    base: '/qhub-ops/'
  }
} : {}

export default {
  ...routerBase,
  head: {
    link: [
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css?family=Montserrat+Alternates' },
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css?family=Lato'}
    ]
  },
  buildModules: [
    '@nuxtjs/markdownit',
    '@nuxtjs/vuetify',
    '@nuxt/typescript-build',
  ],
  markdownit: {
    preset: "default",
    linkify: true,
    breaks: true,
    use: [
      "markdown-it-div",
      "markdown-it-attrs",
    ],
  },
  plugins: [
     { src: '~/plugins/typed', mode: 'client' }, 
     { src: '~/plugins/vuetify', mode: 'client' }
  ],
  generate: {},
  vuetify: {
    customVariables: ['~/assets/variables.scss'],
    defaultAssets: false,
    treeShake: true
  },
};
