import React from "react";
import { Redirect, Switch } from "react-router-dom";
import { RouteWithSubRoutes } from "./util";

export default class Plugins extends React.Component {
  createPlugin = e => {
    //TODO: implement in node or something
    const fs = require("fs-extra");
    const name = window.prompt("What do you want to call your plugin?");
    fs.writeFileSync(
      "./plugins/" + name + ".jsx",
      'import React from "react";'
    );
    this.props.reload();
  };
  switch = React.createRef();
  render() {
    return (
      <React.Fragment>
        <Switch ref={this.switch}>
          {this.props.routes.length > 0 && (
            <Redirect exact from="/plugins" to={this.props.routes[0].path} />
          )}
          {this.props.routes.map((route, i) => {
            return (
              <RouteWithSubRoutes
                key={i}
                setQuery={this.props.setQuery}
                data={this.props.data}
                runHistoryKeyInfo={this.props.runHistoryKeyInfo}
                {...route}
              />
            );
          })}
        </Switch>
      </React.Fragment>
    );
  }
}
