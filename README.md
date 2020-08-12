# qhub: Home

This is the main web application for QHub. This home website will be the interface that hosts the landing page,
any documentation related to the project and its efforts, and finally a way to deploy instances of QHub. 

## Developing

This project uses the `yarn` package manager alongside `nuxtjs`.
Run `yarn` in the root directory to download all the files needed to build.
Make the changes, and then run `yarn run dev` to start a server at `localhost:3000`.

Additionally, you can run `yarn generate` to generate the `dist` folder to test locally
before deploying to github.

## Deploying

`yarn deploy:gh-pages` will deploy the current branches' changes. 
This will be reflected to the github pages website.
