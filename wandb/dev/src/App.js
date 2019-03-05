import React, { lazy, Component, Suspense } from "react";
import { importMDX } from "mdx.macro";
import Postmate from "postmate";
import Plugins from "./Plugins";
import Reports from "./Reports";
import { BrowserRouter as Router, Route } from "react-router-dom";
import { getComponents, plugins, RouteWithSubRoutes } from "./util.js";
import "./App.css";

class App extends Component {
  state = {
    data: null,
    minHeight: 100
  };
  reload = () => {
    this.forceUpdate();
  };
  plugins = () => {
    return getComponents(plugins).map(comp => ({
      path: "/plugins/" + comp.name,
      name: comp.name,
      module: comp.module,
      component: comp.Component
    }));
  };

  async componentDidMount() {
    this.model = new Postmate.Model({
      height: () => document.height || document.body.offsetHeight,
      plugins: () => {
        return this.plugins().map(p => ({ value: p.path, text: p.name }));
      },
      setState: data => {
        this.setState(data);
      },
      setHeight: minHeight => {
        this.setState({ minHeight });
      }
    });
    this.parent = await this.model;
    this.emit("ready", {});
  }
  emit = (event, data) => {
    this.parent.emit(event, data);
  };
  render() {
    this.routes = [
      {
        path: "/plugins",
        component: Plugins,
        routes: this.plugins()
      },
      {
        path: "/reports",
        component: Reports,
        routes: []
      }
    ];
    console.log("Plugs", this.plugins());
    return (
      <div>
        <Suspense fallback={<div>Loading...</div>}>
          <Router>
            <div style={{ height: this.state.minHeight }}>
              {this.routes.map((route, i) => (
                <RouteWithSubRoutes
                  data={this.state.data}
                  reload={this.reload}
                  key={i}
                  {...route}
                />
              ))}
            </div>
          </Router>
        </Suspense>
      </div>
    );
  }
}

export default App;
