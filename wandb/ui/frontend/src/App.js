import React from "react";
import { LiveProvider, LiveEditor, LiveError, LivePreview } from "react-live";
import { ObjectInspector } from "react-inspector";
import "./App.css";

function App(props, scope) {
  return (
    <div className="app row">
      <LiveProvider code={props.code} scope={props.scope}>
        <div className="editor col" style={{ width: "50%" }}>
          <h3>Inputs</h3>
          <ObjectInspector data={props.scope} />
          <h3>Component</h3>
          <LiveEditor />
          <LiveError />
        </div>
        <div className="preview col" style={{ width: "50%" }}>
          <h3>Preview</h3>
          <LivePreview />
        </div>
      </LiveProvider>
    </div>
  );
}

export default App;
