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
        .should('have.attr', 'value', 'Start');
        
        
        /* 
        // Attempt at checking JupyterLab and saving notebook - but too complicated for now
        .click();

      cy.get('div.jp-LauncherCard[data-category="Notebook"] > div.jp-LauncherCard-label[title="Python 3"] > p', { timeout: 20000 })
        .click(); // Launch new Python notebook

      cy.get('div.jp-Notebook textarea').type('print("HELLO"+"QHUB")');

      cy.get('div.jp-NotebookPanel-toolbar > div:nth-child(1) > button').click(); // Save

      */
      

    } else {
      throw new Error("No security_authentication_type env var is set");
    }

  })

})
