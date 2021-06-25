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
});
  

Cypress.Commands.add('loginWithPassword', (username, password) => {
    cy.visit('/hub/home');
  
    cy.get('#username_input')
      .type(username);
  
    cy.get('#password_input')
      .type(password);
  
    cy.get('form').submit();
});


Cypress.Commands.add('runJHubClient', (JHUB_CLIENT_PYTHON_PATH, hub_url, username, password, notebookpath, timeout=20000) => {

  Cypress.config('execTimeout', timeout);

  return cy.exec(
    [
      JHUB_CLIENT_PYTHON_PATH, "-m", "jhub_client", "run", 
      "--hub", hub_url, "--notebook", notebookpath, 
      "--auth-type", "basic", "--validate"
    ].join(" "), 
    {
      env: { JUPYTERHUB_USERNAME: username, JUPYTERHUB_PASSWORD: password } 
    }
  )

});

