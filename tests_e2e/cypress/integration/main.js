const security_authentication_type = Cypress.env('security_authentication_type');

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

      cy.loginWithPassword('example-user', Cypress.env('EXAMPLE_USER_PASSWORD'));
      
    /*   // If multiple profiles are available
       cy.get('h1')
        .should('contain', 'Server Options');  */
      
      cy.get('#start')
        .should('contain', 'My Server')

    }

  })

})
