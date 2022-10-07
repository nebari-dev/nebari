const path = require('path');

const yaml_fields = [
    'security.authentication.type'
];

module.exports = (on, config) => {

    const fs = require('fs');
    const _ = require('lodash');
    const yaml = require('js-yaml');

    let new_config = {};

    try {

        let fileContents = fs.readFileSync(process.env.NEBARI_CONFIG_PATH, 'utf8');
        let data = yaml.load(fileContents);

        console.log(data);

        new_config['env'] = _.fromPairs(
                _.map(yaml_fields,
                    field => ['nebari_'+field.replace(/\./g, '_') , _.get(data, field, '')]
                        )
        );

        new_config['env']['full_path_of_cypress_folder'] = path.resolve(__dirname, "..");

    }
    catch (e) {
        console.log(e);
    }

    return new_config;
  };
