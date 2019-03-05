import React from "react";
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
  render() {
    return (
      <React.Fragment>
        <div>
          {this.props.routes.map((route, i) => (
            <RouteWithSubRoutes key={i} {...route} />
          ))}
        </div>
      </React.Fragment>
    );
  }
}
