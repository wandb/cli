import React from 'react';
import {scaleLinear} from 'd3-scale';
import {XYPlot, DecorativeAxis, LineSeries} from 'react-vis';
import {
  convertValue,
  getRunValue,
  displayValue,
  filterKeyFromString,
  filtersForAxis,
} from '../util/runhelpers.js';
import {Form} from 'semantic-ui-react';
import {registerPanelClass} from '../util/registry.js';
import _ from 'lodash';
import * as d3 from 'd3';
import {addFilter, setHighlight} from '../actions/run';

const DEFAULT_DOMAIN = {min: Infinity, max: -Infinity};
const MARGIN = {
  left: 10,
  right: 10,
  top: 10,
  bottom: 10,
};
function setupDomains(data) {
  // begin by figuring out the domain of each of the columns
  const domains = data.reduce((res, row) => {
    Object.keys(row).forEach(key => {
      if (key === 'name') {
        return false;
      }
      if (!res[key]) {
        res[key] = {...DEFAULT_DOMAIN};
      }
      res[key] = {
        min: Math.min(res[key].min, row[key]),
        max: Math.max(res[key].max, row[key]),
      };
    });
    return res;
  }, {});
  // use that to generate columns that map the data to a unit scale
  const scales = Object.keys(domains).reduce((res, key) => {
    const domain = domains[key];
    res[key] = scaleLinear()
      .domain([domain.min, domain.max])
      .range([0, 1]);
    return res;
  }, {});

  // break each object into an array and rescale it
  const mappedData = data.map(row => {
    return Object.keys(row)
      .filter(key => key !== 'name')
      .map(key => ({
        x: key,
        y: scales[key](Number(row[key])),
      }));
  });
  return [mappedData, domains];
}

class ParallelCoordinates extends React.Component {
  constructor(props) {
    super(props);
    this.data = [];
    this.mappedData = [];
    this.domains = [];
  }

  componentDidMount() {}

  componentWillReceiveProps(nextProps) {
    if (nextProps.runs) {
      this.data = this.props.runs.map(run => {
        let row = {name: run.name};
        for (var col of this.props.cols) {
          row[col] = getRunValue(run, col);
        }
        return row;
      });
      this.data = this.data.filter(row =>
        d3.values(row).every(val => val !== null && val !== NaN),
      );
      [this.mappedData, this.domains] = setupDomains(this.data);
    }
  }
  render() {
    return (
      <XYPlot
        width={1024}
        height={420}
        xType="ordinal"
        margin={MARGIN}
        className="parallel-coordinates-example">
        {this.mappedData.map((series, index) => {
          return <LineSeries data={series} key={`series-${index}`} />;
        })}
        {(this.mappedData[0] || []).map((cell, index) => {
          return (
            <DecorativeAxis
              key={`${index}-axis`}
              axisStart={{x: cell.x, y: 0}}
              axisEnd={{x: cell.x, y: 1}}
              axisDomain={[this.domains[cell.x].min, this.domains[cell.x].max]}
            />
          );
        })}
      </XYPlot>
    );
  }
}
class ParCoordPanel extends React.Component {
  static type = 'Parallel Coordinates Plot Viz';
  static options = {
    width: 16,
  };

  static validForData(data) {
    return !_.isNil(data.filtered);
  }

  constructor(props) {
    super(props);
    this.select = {};
  }

  _setup(props, nextProps) {
    let {dimensions} = nextProps.config;
    if (dimensions && nextProps.selections !== props.selections) {
      this.select = {};
      for (var dim of dimensions) {
        this.select[dim] = filtersForAxis(nextProps.selections, dim);
      }
    }
  }

  componentWillMount() {
    this._setup({}, this.props);
  }

  componentWillReceiveProps(nextProps) {
    this._setup(this.props, nextProps);
  }

  renderConfig() {
    let {filtered, keys, axisOptions} = this.props.data;
    return (
      <Form>
        <Form.Dropdown
          label="Dimensions"
          placeholder="Dimensions"
          fluid
          multiple
          search
          selection
          options={axisOptions}
          value={this.props.config.dimensions}
          onChange={(e, {value}) =>
            this.props.updateConfig({
              ...this.props.config,
              dimensions: value,
            })
          }
        />
      </Form>
    );
    return;
  }

  renderNormal() {
    let {dimensions} = this.props.config;
    if (this.props.data.filtered && dimensions) {
      return (
        <ParallelCoordinates
          cols={dimensions}
          runs={this.props.data.filtered}
          select={this.select}
          highlight={this.props.highlight}
          onBrushEvent={(axis, low, high) => {
            this.props.batchActions([
              addFilter('select', filterKeyFromString(axis), '>', low),
              addFilter('select', filterKeyFromString(axis), '<', high),
            ]);
          }}
          onMouseOverEvent={runName => {
            this.props.setHighlight(runName);
          }}
          onMouseOutEvent={() => this.props.setHighlight(null)}
        />
      );
    } else {
      return <p>Please configure dimensions first</p>;
    }
  }

  render() {
    if (this.props.configMode) {
      return (
        <div>
          {this.renderNormal()}
          {this.renderConfig()}
        </div>
      );
    } else {
      return this.renderNormal();
    }
  }
}
registerPanelClass(ParCoordPanel);

export default ParCoordPanel;
