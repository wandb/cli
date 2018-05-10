import * as React from 'react';
import {Confirm, Button, Icon, Popup, Grid} from 'semantic-ui-react';
import RunSelectTags from './RunSelectTags';

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
      this.setState({options: nextProps.tags});
    }
  }

  batchTags = (e: any, tags: string[], add: boolean = true): void => {
    e.preventDefault();

    setTimeout(() => {
      this.setState({
        isOpen: false,
        showConfirm: true,
        confirmText:
          (add ? 'Add' : 'Remove') +
          " '" +
          tags.join(', ') +
          "' tag(s) " +
          (add ? 'to' : 'from') +
          ' selected runs?',
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
                  <RunSelectTags
                    add={true}
                    batchTags={this.batchTags}
                    tags={this.state.options}
                  />
                </Grid.Column>
              </Grid.Row>
              <Grid.Row>
                <Grid.Column>
                  <RunSelectTags
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
