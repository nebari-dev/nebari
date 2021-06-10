const { divide } = require("lodash");

const security_authentication_type = Cypress.env('qhub_security_authentication_type');


describe('First Test', () => {

  it('Check QHub login page is running', () => {

    if (security_authentication_type == 'Auth0') {

      cy.visit('/hub/home');

      cy.get('#login-main > div.service-login > a')
        .should('contain', 'Sign in with Auth0');

    } else if (security_authentication_type == 'GitHub') {

      cy.visit('/hub/home');

      cy.get('#login-main > div.service-login > a')
        .should('contain', 'Sign in with GitHub');

    } else if (security_authentication_type == 'password') {

      cy.loginWithPassword(Cypress.env('EXAMPLE_USER_NAME') || 'example-user', Cypress.env('EXAMPLE_USER_PASSWORD'));

      // Start my Jupyter server
      
      cy.get('#start')
        .should('contain', 'My Server').click();

       cy.get('h1')
        .should('contain', 'Server Options');

      cy.get('input.btn.btn-jupyter')
        .should('have.attr', 'value', 'Start').click();

      // Minimal check that JupyterLab has opened

      cy.get('div#jp-MainLogo', { timeout: 30000 }).should('exist');

      // Stop my Jupyter server - must do this so PVC can be destroyed on Minikube

      cy.visit('/hub/home');

        // wait because otherwise event handler is not yet registered
        // 'Correct' solution is here: https://www.cypress.io/blog/2019/01/22/when-can-the-test-click/
      cy.get('#stop')
        .should('contain', 'Stop My Server').wait(500).click();

      cy.get('#start', { timeout: 30000 })
        .should('contain', 'Start My Server');

    } else {
      throw new Error("No security_authentication_type env var is set");
    }

  })

})
