import path from "path";
import minimatch from "minimatch";
import React, { lazy, Component, Suspense } from "react";
import { Route } from "react-router-dom";
export const getComponents = req =>
  req
    .keys()
    .filter(minimatch.filter("!node_modules"))
    .filter(key => !/^_/.test(path.basename(key)))
    .map(key => ({
      key,
      name: path.basename(key, path.extname(key)),
      module: req(key),
      Component: req(key).default || req(key)
    }))
    .map(component => {
      console.log("Comps", component);
      return component;
    })
    .filter(component => typeof component.Component === "function");

export const plugins = require.context("./plugins", true, /\.(js|md|mdx|jsx)$/);
export function RouteWithSubRoutes(route) {
  return (
    <Route
      path={route.path}
      render={props => (
        <route.component
          {...props}
          reload={route.reload}
          routes={route.routes}
        />
      )}
    />
  );
}
