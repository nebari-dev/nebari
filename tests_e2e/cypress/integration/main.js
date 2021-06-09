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
      
      cy.get('#start')
        .should('contain', 'My Server').click();

       cy.get('h1')
        .should('contain', 'Server Options');

      cy.get('input.btn.btn-jupyter')
        .should('have.attr', 'value', 'Start').click();

      cy.get('div#jp-MainLogo', { timeout: 20000 }).should('exist');
        

    } else {
      throw new Error("No security_authentication_type env var is set");
    }

  })

})
