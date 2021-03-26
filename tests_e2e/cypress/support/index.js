// ***********************************************************
// This example support/index.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
// import './commands'

// Alternatively you can use CommonJS syntax:
// require('./commands')

Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
  })
  

/* Cypress.Commands.add('loginAuth0', (username, password) => {
    Cypress.log({
        name: 'loginAuth0',
    });

    const options = {
        method: 'POST',
        url: 'https://'+ Cypress.env('AUTH0_DOMAIN') + '/oauth/token',
        body: {
            grant_type: 'password',
            username: username,
            password: password,
            audience: 'https://'+ Cypress.env('AUTH0_DOMAIN') + '/api/v2/',
            scope: 'openid profile email',
            client_id: Cypress.env('AUTH0_CLIENT_ID'),
            client_secret: Cypress.env('AUTH0_CLIENT_SECRET'),
        },
    };

    cy.request(options)
}); */
