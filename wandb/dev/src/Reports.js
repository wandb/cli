import React from "react";
export default function Reports() {
  return (
    <React.Fragment>
      <h1>Reports</h1>
      <select>
        {this.props.reports.map(p => (
          <option>{p.name}</option>
        ))}
        <option>Create New</option>
      </select>
    </React.Fragment>
  );
}
