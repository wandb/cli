import * as React from 'react';
import {Button, Dropdown, Segment} from 'semantic-ui-react';

interface RunSelectTagsProps {
  add: boolean;
  batchTags(e: any, tags: string[], add: boolean): void;
  tags?: any;
}

interface RunSelectTagsState {
  options?: any;
  currentValues?: string[];
}

export default class RunSelectTags extends React.Component<
  RunSelectTagsProps,
  RunSelectTagsState
> {
  constructor(props: RunSelectTagsProps) {
    super(props);
    this.state = {
      options: props.tags,
      currentValues: [],
    };
  }

  handleAddition = (e: any, {value}: any): void => {
    this.setState({
      options: [{text: value, value}, ...this.state.options],
    });
  };

  handleChange = (e: any, {value}: any): void =>
    this.setState({currentValues: value});

  render() {
    return (
      <span>
        <Dropdown
          options={this.state.options}
          placeholder="Choose tag(s)"
          search
          selection
          multiple
          fluid
          closeOnChange={true}
          allowAdditions={this.props.add}
          value={this.state.currentValues}
          onAddItem={this.handleAddition}
          onChange={this.handleChange}
        />
        <Button
          fluid
          type="submit"
          disabled={
            !this.state.currentValues || this.state.currentValues.length === 0
          }
          onClick={e => {
            this.state.currentValues &&
              this.props.batchTags(e, this.state.currentValues, this.props.add);
            this.setState({currentValues: []});
          }}>
          {this.props.add ? 'Add' : 'Remove'}
        </Button>
      </span>
    );
  }
}
