import React, { Component } from 'react';
import { Menu, Item, Separator, Submenu, MenuProvider, contextMenu } from 'react-contexify';
import 'react-contexify/dist/ReactContexify.min.css';

class SettingsPanel extends Component {
  constructor(props) {
    /* Create state elements and initialize configuration. */
    super(props);
    this.state = {
      sampleText : "hello world!"
    }
  }
  render () {
    return (
      <div>
        <p>{this.state.sampleText}</p>
        <p>{this.props.propText}</p>
        <p>{this.props.propWidth}px wide</p>
      </div>
    );
  }
}
export default SettingsPanel;