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

const path = require('path');

Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false;
});


Cypress.Commands.add('loginWithPassword', (username, password) => {
    cy.visit('/hub/home');

    cy.get('#login-main > div.service-login > a')
        .should('contain', 'Sign in with Keycloak').click();

    cy.get('input#username')
      .type(username);

    cy.get('input#password')
      .type(password);

    cy.get('form').submit();
});
