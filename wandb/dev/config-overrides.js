const { getBabelLoader, addWebpackAlias } = require("customize-cra");
const path = require("path");
module.exports = (config, env) => {
  const babelLoader = getBabelLoader(config);
  config.module.rules.map(rule => {
    if (typeof rule.test !== "undefined" || typeof rule.oneOf === "undefined") {
      return rule;
    }
    rule.oneOf.unshift({
      test: /\.mdx$/,
      use: [
        {
          loader: babelLoader.loader,
          options: babelLoader.options
        },
        "mdx-loader"
      ]
    });
    return rule;
  });
  addWebpackAlias({
    wandb: path.resolve(__dirname)
  });

  return config;
};
