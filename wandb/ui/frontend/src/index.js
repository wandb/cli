import React from "react";
import ReactDOM from "react-dom";
import "./index.css";
import App from "./App";
import * as serviceWorker from "./serviceWorker";
import defaultScope from "./scope";

const scope = Object.assign(defaultScope, window.initialScope || {});
const code = scope.code;
delete scope.code;
ReactDOM.render(
  <App code={code} scope={scope} />,
  document.getElementById("root")
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
