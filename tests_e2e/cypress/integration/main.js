let do_login_password = (username, password) => {
    
  cy.visit('/hub/home');

  cy.get('#username_input')
    .type(username);

  cy.get('#password_input')
    .type(password);

  cy.get('form').submit();

};


let do_login_auth0 = (username, password) => {
    
  cy.visit('/hub/home');

  cy.get('#login-main > div.service-login > a')
    .should('contain', 'Sign in with Auth0');

// https://auth0.com/blog/end-to-end-testing-with-cypress-and-auth0/
// Says we should do a request directly

  const body = {
        grant_type: 'password',
        username: username,
        password: password,
        audience: 'https://'+ Cypress.env('AUTH0_DOMAIN') + '/api/v2/',
        scope: 'openid profile email',
        client_id: Cypress.env('AUTH0_CLIENT_ID'),
        client_secret: Cypress.env('AUTH0_CLIENT_SECRET'),
  };
  

  cy.request('POST', 
  'https://'+ Cypress.env('AUTH0_DOMAIN') + '/oauth/token',
   body).and((resp) => {
        cy.log(resp.body);
        let body = resp.body;
        cy.log(body);
        const {access_token, expires_in, id_token} = body;
        const auth0State = {
          nonce: '',
          state: 'some-random-state'
        };
        const callbackUrl = `/hub/oauth_callback?access_token=${access_token}&scope=openid&id_token=${id_token}&expires_in=${expires_in}&token_type=Bearer&state=${auth0State.state}`;
        cy.visit(callbackUrl, {
          onBeforeLoad(win) {
            win.document.cookie = 'com.auth0.auth.some-random-state=' + JSON.stringify(auth0State);
          }
        });
      })
  
// Alternative is to click through auth0 website, but need a cypress.json setting to disable security.
  /*  .click();

  cy.get('input#1-email')
    .type(username);

  cy.get('div > input[type="password"]')
    .type(password);

  cy.get('span.auth0-label-submit').click(); */

};

describe('First Test', () => {

  it('Check QHub login page is running', () => {

    cy.visit('/hub/home');

    cy.get('#login-main > div.service-login > a')
      .should('contain', 'Sign in with Auth0');


    // do_login_password('example-user', 'example-user')
    // do_login_auth0('example-user', 'example-user');

    /*cy.get('h1')
      .should('contain', 'Server Options');
    */
  })

})
