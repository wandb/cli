import React, { lazy, Component, Suspense } from "react";
import Postmate from "postmate";
import Plugins from "./Plugins";
import Reports from "./Reports";
import { Router, Redirect, Switch } from "react-router-dom";
import { getComponents, plugins, RouteWithSubRoutes } from "./util.js";
import { createBrowserHistory } from "history";
import { Loader, Segment, Dimmer } from "semantic-ui-react";
import "./App.css";

const history = createBrowserHistory();
class App extends Component {
  state = {
    connected: false,
    data: null,
    runHistoryKeyInfo: null,
    minHeight: 100
  };
  reload = () => {
    this.plugins(true);
    this.forceUpdate();
  };
  plugins = (reload = false) => {
    if (reload || !this._plugins) {
      this._plugins = getComponents(plugins).map(comp => ({
        path: "/plugins/" + comp.name,
        name: comp.name,
        module: comp.module,
        query: comp.query,
        component: comp.Component
      }));
    }
    return this._plugins;
  };

  setInitialQuery(path) {
    path = path || history.location.pathname;
    const comp = this.plugins().find(p => p.path === path);
    if (comp && comp.query) {
      console.log("Sending query", comp.query);
      this.setQuery(comp.query);
    }
  }

  componentWillMount() {
    history.listen((location, action) => {
      this.setInitialQuery(location.pathname);
    });
    this.setInitialQuery();
  }

  async componentDidMount() {
    window.onbeforeunload = () => {
      this.emit("unmounting");
    };
    this.model = new Postmate.Model({
      height: () => document.height || document.body.offsetHeight,
      plugins: () => {
        return this.plugins().map(p => ({ value: p.path, text: p.name }));
      },
      setState: data => {
        console.log("Setting state..", data);
        this.setState(data);
      },
      navigate: path => {
        history.push(path);
      }
    });
    this.parent = await this.model;
    this.setState({ connected: true });
    this.emit("ready", {});
  }
  emit = (event, data) => {
    if (this.parent) {
      this.parent.emit(event, data);
    }
  };
  setQuery = query => {
    this.emit("setQuery", query);
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
    return (
      <div>
        <Suspense fallback={<div>Loading...</div>}>
          <Router history={history} onChange={this.setInitialQuery}>
            {this.state.connected ? (
              <Switch>
                <Redirect exact from="/" to="/plugins" />
                {this.routes.map((route, i) => (
                  <RouteWithSubRoutes
                    data={this.state.data}
                    runHistoryKeyInfo={this.state.runHistoryKeyInfo}
                    currentHeight={this.state.currentHeight}
                    setQuery={this.setQuery}
                    reload={this.reload}
                    key={i}
                    {...route}
                  />
                ))}
              </Switch>
            ) : (
              <Segment style={{ minHeight: 250 }}>
                <Dimmer active inverted>
                  <Loader size="large">Connecting to wandb...</Loader>
                </Dimmer>
              </Segment>
            )}
          </Router>
        </Suspense>
      </div>
    );
  }
}

export default App;
