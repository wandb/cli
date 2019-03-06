const { getBabelLoader } = require("customize-cra");
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
  return config;
};
