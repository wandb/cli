import React from 'react';
import {Label, Button} from 'semantic-ui-react';

export default class Tags extends React.Component {
  render() {
    return this.props.tags.map(tag => (
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
            this.props.removeTag(tag);
          }}
        />
      </Button.Group>
    ));
  }
}
