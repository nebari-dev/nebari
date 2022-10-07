const { divide } = require("lodash");

const security_authentication_type = Cypress.env('nebari_security_authentication_type');

const EXAMPLE_USER_NAME = Cypress.env('EXAMPLE_USER_NAME') || 'example-user';

const EXAMPLE_USER_PASSWORD = Cypress.env('EXAMPLE_USER_PASSWORD');


describe('First Test', () => {

  if (security_authentication_type == 'Auth0') {

    it('Check Auth0 login page is running', () => {

      cy.visit('/hub/home');

      cy.get('#login-main > div.service-login > a')
        .should('contain', 'Sign in with Keycloak').click();

      cy.get('a#social-auth0')
        .should('contain', 'auth0');

    })

  } else if (security_authentication_type == 'GitHub') {

    it('Check GitHub login page is running', () => {

      cy.visit('/hub/home');

      cy.get('#login-main > div.service-login > a')
        .should('contain', 'Sign in with Keycloak').click();

      cy.get('a#social-github')
        .should('contain', 'github');


    })

  } else if (security_authentication_type == 'password') {

    it('Check QHub login and start JupyterLab', () => {

      cy.loginWithPassword(EXAMPLE_USER_NAME, EXAMPLE_USER_PASSWORD);

      // Start my Jupyter server

      cy.get('#start')
        .should('contain', 'My Server').click();

        cy.get('h1')
        .should('contain', 'Server Options');

      cy.get('input.btn.btn-jupyter')
        .should('have.attr', 'value', 'Start').click();

      // Minimal check that JupyterLab has opened
      cy.get('div#jp-MainLogo', { timeout: 60000 }).should('exist').wait(500);

      // Click VS Code Launcher exists
      cy.get('div.jp-LauncherCard[title="VS Code [↗]"]').should('exist');

      // Stop my Jupyter server - must do this so PVC can be destroyed on Minikube
      cy.visit('/hub/home');

      // wait because otherwise event handler is not yet registered
      // 'Correct' solution is here: https://www.cypress.io/blog/2019/01/22/when-can-the-test-click/
      cy.get('#stop')
        .should('contain', 'Stop My Server').wait(1000).click();

      cy.get('#start', { timeout: 40000 })
        .should('contain', 'Start My Server');

      // Visit Conda-Store

      cy.visit('/conda-store/login/');

      cy.get('body > nav > a')
        .contains('conda-store')
        .should('have.attr', 'href');

      // Visit Grafana Monitoring - user must have an email address in Keycloak

      cy.visit('/monitoring/dashboards');

      cy.get('div.page-header h1', { timeout: 20000 }).should('contain', 'Dashboards');

      // Visit Keycloak User Profile

      cy.visit('/auth/realms/qhub/account/#/personal-info');

      cy.get('input#user-name', { timeout: 20000 }).should('have.value', EXAMPLE_USER_NAME);
    })

  } else {
    throw new Error("No security_authentication_type env var is set");
  }

})
