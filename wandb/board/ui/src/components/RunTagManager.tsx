import * as React from 'react';
import {Confirm, Button, Icon, Popup, Grid, Dropdown} from 'semantic-ui-react';

interface SelectTagsProps {
  add: boolean;
  batchTags(e: any, tags: string[], add: boolean): void;
  tags?: any;
}

interface SelectTagsState {
  options?: any;
  currentValues?: string[];
}

class SelectTags extends React.Component<SelectTagsProps, SelectTagsState> {
  constructor(props: SelectTagsProps) {
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
      <Button.Group>
        <Dropdown
          options={this.state.options}
          placeholder="Choose tag(s)"
          search
          selection
          button
          multiple
          allowAdditions={this.props.add}
          value={this.state.currentValues}
          onAddItem={this.handleAddition}
          onChange={this.handleChange}
        />
        <Button
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
      </Button.Group>
    );
  }
}

interface RunTagManagerProps {
  selectedRuns: object[];
  modifyRuns(variables: any): void;
  tags: string[];
}

interface RunTagManagerState {
  isOpen?: boolean;
  showConfirm?: boolean;
  handleCancel?(e: any): void;
  handleOpen?(e: any): void;
  handleConfirm?(e: any): void;
  confirmText?: string;
  confirmButton?: string;
  options?: any;
}

export default class RunTagManager extends React.Component<
  RunTagManagerProps,
  RunTagManagerState
> {
  constructor(props: RunTagManagerProps) {
    super(props);
    this.state = {
      isOpen: false,
      showConfirm: false,
      options: [],
    };
  }

  handleOpenPopup = () => {
    this.setState({isOpen: true});
  };

  handleClosePopup = () => {
    this.setState({isOpen: false});
  };

  componentWillReceiveProps(nextProps: RunTagManagerProps) {
    if (nextProps.tags !== this.props.tags) {
      let tags = nextProps.tags.map((item: string) => {
        return {text: item, value: item};
      });
      this.setState({options: tags});
    }
  }

  batchTags = (e: any, tags: string[], add: boolean = true): void => {
    e.preventDefault();

    setTimeout(() => {
      this.setState({
        isOpen: false,
        showConfirm: true,
        confirmText:
          'Are you sure you would like to ' +
          (add ? 'add' : 'remove') +
          ' `' +
          tags.join(', ') +
          '` tag(s) to selected runs?',
        confirmButton:
          (add ? 'Add to' : 'Remove from') +
          ` ${this.props.selectedRuns.length} run(s)`,

        handleConfirm: e => {
          e.preventDefault();
          this.props.modifyRuns({
            ids: this.props.selectedRuns.map((run: any) => run.id),
            tags: tags,
            operation: add,
          });
          this.setState({
            showConfirm: false,
          });
        },
        handleCancel: e => {
          e.preventDefault();
          this.setState({
            showConfirm: false,
          });
        },
      });
    });
  };

  render() {
    return (
      <span>
        <Confirm
          open={this.state.showConfirm}
          onCancel={this.state.handleCancel}
          onConfirm={this.state.handleConfirm}
          content={this.state.confirmText}
          confirmButton={this.state.confirmButton}
        />
        <Popup
          trigger={
            <Button
              icon="lightning"
              content="Batch Actions"
              disabled={this.props.selectedRuns.length === 0}
            />
          }
          on="click"
          onOpen={this.handleOpenPopup}
          onClose={this.handleClosePopup}
          open={this.state.isOpen}
          content={
            <Grid>
              <Grid.Row>
                <Grid.Column>
                  <Button onClick={e => this.batchTags(e, ['hidden'])} fluid>
                    <Icon name="hide" />
                    Hide {this.props.selectedRuns.length} run(s)
                  </Button>
                </Grid.Column>
              </Grid.Row>
              <Grid.Row>
                <Grid.Column>
                  <Button
                    onClick={e => this.batchTags(e, ['hidden'], false)}
                    fluid>
                    <Icon name="unhide" />
                    Unhide {this.props.selectedRuns.length} run(s)
                  </Button>
                </Grid.Column>
              </Grid.Row>
              <Grid.Row>
                <Grid.Column>
                  <SelectTags
                    add={true}
                    batchTags={this.batchTags}
                    tags={this.state.options}
                  />
                </Grid.Column>
              </Grid.Row>
              <Grid.Row>
                <Grid.Column>
                  <SelectTags
                    add={false}
                    batchTags={this.batchTags}
                    tags={this.state.options}
                  />
                </Grid.Column>
              </Grid.Row>
            </Grid>
          }
          position="top left"
        />
      </span>
    );
  }
}
