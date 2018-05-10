import React from 'react';
import {Label, Button, Confirm, Popup} from 'semantic-ui-react';
import RunSelectTags from './RunSelectTags';
import './Tags.css';

export default class Tags extends React.Component {
  state = {open: false, showPopup: false};

  show = tag => this.setState({open: true, tag: tag});
  handleConfirm = () => {
    this.modifyTags([this.props.id], [this.state.tag], false);
    this.setState({open: false});
  };
  handleCancel = () => this.setState({open: false});

  modifyTags = (ids, tags, operation) => {
    this.props.modifyRuns({
      ids,
      tags,
      operation,
    });
  };

  addTags = (e, tags) => {
    this.modifyTags([this.props.id], tags, true);
    this.setState({showPopup: false});
  };

  render() {
    let classes = 'tagsWrapper' + (this.state.showPopup ? ' popupOpened' : '');
    return (
      <span className={classes}>
        <Confirm
          open={this.state.open}
          onCancel={this.handleCancel}
          onConfirm={this.handleConfirm}
          content={
            "Are you sure you want to remove '" + this.state.tag + "' tag?"
          }
          confirmButton="Remove"
        />
        {this.props.tags.map(tag => (
          <Button.Group size="mini" key={tag}>
            <Button
              className="filter"
              style={{
                cursor: this.props.addFilter ? 'pointer' : 'auto',
              }}
              onClick={() => this.props.addFilter && this.props.addFilter(tag)}>
              {tag}
            </Button>
            <Button
              negative
              className="delete"
              icon="trash"
              onClick={e => {
                // prevents triggering Popup click event, that will cause "onOpen" event to be called
                e.stopPropagation();
                this.show(tag);
              }}
            />
          </Button.Group>
        ))}
        <Popup
          trigger={
            <Button
              icon="plus"
              className="addButton"
              circular
              content="Add tag(s)"
              size="mini"
            />
          }
          on="click"
          open={this.state.showPopup}
          onOpen={() => this.setState({showPopup: true})}
          onClose={() => this.setState({showPopup: false})}
          content={
            <RunSelectTags
              add={true}
              batchTags={this.addTags}
              tags={this.props.options}
            />
          }
          position="top left"
        />
      </span>
    );
  }
}
