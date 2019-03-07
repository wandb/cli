import path from "path";
import minimatch from "minimatch";
import React, { lazy, Component, Suspense } from "react";
import { Route } from "react-router-dom";
export const getComponents = req =>
  req
    .keys()
    .filter(minimatch.filter("!node_modules"))
    .filter(key => !/^_/.test(path.basename(key)))
    .map(key => {
      const mod = req(key);
      const comp = mod.default || mod;
      const query = comp.query || mod.query;
      return {
        key,
        name: path.basename(key, path.extname(key)),
        module: mod,
        query: query,
        Component: comp
      };
    })
    .filter(component => typeof component.Component === "function");
export function toNivo(data, yKey, xKey = "_step") {
  if (!data || data.histories == null) {
    return [];
  }
  console.log("TF", data.histories.data[0]);
  return data.histories.data.map(ob => {
    return {
      id: ob.name,
      data: ob.history.map(h => ({ x: h[xKey], y: h[yKey] }))
    };
  });
}
export const plugins = require.context(
  "./wandb/plugins",
  true,
  /\.(js|md|mdx|jsx)$/
);
export function RouteWithSubRoutes(route) {
  return (
    <Route
      path={route.path}
      render={props => {
        return (
          <div style={{ height: route.currentHeight }}>
            <route.component {...props} {...route} />
          </div>
        );
      }}
    />
  );
}
