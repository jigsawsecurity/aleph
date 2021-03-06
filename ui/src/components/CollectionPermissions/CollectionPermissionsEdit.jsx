import React, {Component} from 'react';
import { Checkbox, Button } from '@blueprintjs/core';
import {connect} from 'react-redux';
import {defineMessages, FormattedMessage, injectIntl} from 'react-intl';

import Role from 'src/components/common/Role';
import {showSuccessToast} from "../../app/toast";
import {updateCollectionPermissions} from "../../actions";

import './CollectionPermissionsEdit.css';

const messages = defineMessages({
  save_success: {
    id: 'collection.edit.save_success',
    defaultMessage: 'Your changes are saved.',
  },
});

class PermissionRow extends Component {
  render() {
    const { permission, onToggle } = this.props;
    return (<tr>
      <td>
        {permission.role.name}
      </td>
      <td className='other-rows'>
        <Checkbox checked={permission.read}
                  onChange={() => onToggle(permission, 'read')} />
      </td>
      <td className='other-rows'>
        <Checkbox checked={permission.write}
                  onChange={() => onToggle(permission, 'write')} />
      </td>
    </tr>);
  }
}

class CollectionPermissionsEdit extends Component {

  constructor(props) {
    super(props);
    this.state = {permissions: []};

    this.onAddRole = this.onAddRole.bind(this);
    this.onToggle = this.onToggle.bind(this);
    this.onSave = this.onSave.bind(this);
  }

  filterPermissions(type) {
    const { permissions } = this.props;
    return permissions.filter((perm) =>
      perm.role.type === type
    );
  }

  onAddRole(role) {
    const { permissions } = this.props;
    permissions.push({role: role, read: true, write: false});
    this.setState({permissions: permissions});
  }

  onToggle(permission, flag) {
    const permissions = this.props.permissions.map((perm) => {
      if (perm.role.id === permission.role.id) {
        perm[flag] = !perm[flag];
      }
      return perm;
    });

    this.setState({permissions: permissions});
  }

  async onSave() {
    const { intl, collection, updateCollectionPermissions } = this.props;
    const { permissions } = this.state;

    await updateCollectionPermissions(collection.id, permissions);
    showSuccessToast(intl.formatMessage(messages.save_success));
  }

  render() {
    const { permissions } = this.props;
    const exclude = permissions.map((perm) => perm.role.id);

    return (
      <div className="CollectionPermissions">
        <table className="settings-table">
          <thead>
          <tr key={0}>
            <th/>
            <th>
              <FormattedMessage id="collection.edit.permissionstable.view"
                                defaultMessage="View"/>
            </th>
            <th>
              <FormattedMessage id="collection.edit.permissionstable.edit"
                                defaultMessage="Edit"/>
            </th>
          </tr>
          </thead>
          <tbody>
          {this.filterPermissions('system').map((permission) =>
            <PermissionRow key={permission.role.id}
                          permission={permission}
                          onToggle={this.onToggle} />
          )}
          <tr key={'groups'}>
            <td className='header-topic' colSpan="3">
              <FormattedMessage id="collection.edit.groups"
                                defaultMessage="Groups"/>
            </td>
          </tr>
          {this.filterPermissions('group').map((permission) =>
            <PermissionRow key={permission.role.id}
                          permission={permission}
                          onToggle={this.onToggle} />
          )}
          <tr key={'users'}>
            <td className='header-topic' colSpan="3">
              <FormattedMessage id="collection.edit.users"
                                defaultMessage="Users"/>
            </td>
          </tr>
          {this.filterPermissions('user').map((permission) =>
            <PermissionRow key={permission.role.id}
                          permission={permission}
                          onToggle={this.onToggle} />
          )}
          <tr key="add">
            <td colSpan="3">
              <Role.Select onSelect={this.onAddRole}
                          exclude={exclude} />
            </td>
          </tr>
          </tbody>
        </table>
        <div className="save">
          <Button className="pt-intent-primary pt-large" onClick={this.onSave}>
            <FormattedMessage id="collection.info.permissions.update"
                              defaultMessage="Save"/>
          </Button>
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state, ownProps) => {
  return {};
};

export default connect(mapStateToProps, {updateCollectionPermissions})(injectIntl(CollectionPermissionsEdit));