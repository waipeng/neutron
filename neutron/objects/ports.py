# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import netaddr
from oslo_serialization import jsonutils
from oslo_versionedobjects import base as obj_base
from oslo_versionedobjects import fields as obj_fields

from neutron.common import utils
from neutron.db import api as db_api
from neutron.db.models import dns as dns_models
from neutron.db.models import securitygroup as sg_models
from neutron.db import models_v2
from neutron.db.qos import models as qos_models
from neutron.objects import base
from neutron.objects import common_types
from neutron.objects.db import api as obj_db_api
from neutron.plugins.ml2 import models as ml2_models


class PortBindingBase(base.NeutronDbObject):

    foreign_keys = {
        'Port': {'port_id': 'id'},
    }

    @classmethod
    def modify_fields_to_db(cls, fields):
        result = super(PortBindingBase, cls).modify_fields_to_db(fields)
        if 'vif_details' in result:
            result['vif_details'] = (
                cls.filter_to_json_str(result['vif_details']))
        return result

    @classmethod
    def modify_fields_from_db(cls, db_obj):
        fields = super(PortBindingBase, cls).modify_fields_from_db(db_obj)
        if 'vif_details' in fields:
            if fields['vif_details']:
                fields['vif_details'] = jsonutils.loads(fields['vif_details'])
            if not fields['vif_details']:
                fields['vif_details'] = None
        return fields


@obj_base.VersionedObjectRegistry.register
class PortBinding(PortBindingBase):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = ml2_models.PortBinding

    fields = {
        'port_id': obj_fields.UUIDField(),
        'host': obj_fields.StringField(),
        'profile': obj_fields.StringField(),
        'vif_type': obj_fields.StringField(),
        'vif_details': obj_fields.DictOfStringsField(nullable=True),
        'vnic_type': obj_fields.StringField(),
    }

    primary_keys = ['port_id']


@obj_base.VersionedObjectRegistry.register
class DistributedPortBinding(PortBindingBase):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = ml2_models.DistributedPortBinding

    fields = {
        'port_id': obj_fields.UUIDField(),
        'host': obj_fields.StringField(),
        'profile': obj_fields.StringField(),
        'vif_type': obj_fields.StringField(),
        'vif_details': obj_fields.DictOfStringsField(nullable=True),
        'vnic_type': obj_fields.StringField(),
        # NOTE(ihrachys): Fields below are specific to this type of binding. In
        # the future, we could think of converging different types of bindings
        # into a single field
        'status': obj_fields.StringField(),
        'router_id': obj_fields.StringField(nullable=True),
    }

    primary_keys = ['host', 'port_id']


@obj_base.VersionedObjectRegistry.register
class PortBindingLevel(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = ml2_models.PortBindingLevel

    primary_keys = ['port_id', 'host', 'level']

    fields = {
        'port_id': obj_fields.UUIDField(),
        'host': obj_fields.StringField(),
        'level': obj_fields.IntegerField(),
        'driver': obj_fields.StringField(nullable=True),
        'segment': obj_fields.ObjectField(
            'NetworkSegment', nullable=True
        ),
    }

    synthetic_fields = ['segment']

    foreign_keys = {
        'Port': {'port_id': 'id'},
    }

    @classmethod
    def get_objects(cls, context, _pager=None, validate_filters=True,
                    **kwargs):
        if not _pager:
            _pager = base.Pager()
        if not _pager.sorts:
            # (NOTE) True means ASC, False is DESC
            _pager.sorts = [('port_id', True), ('level', True)]
        return super(PortBindingLevel, cls).get_objects(
            context, _pager, validate_filters, **kwargs)


@obj_base.VersionedObjectRegistry.register
class IPAllocation(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = models_v2.IPAllocation

    fields = {
        'port_id': obj_fields.UUIDField(nullable=True),
        'subnet_id': obj_fields.UUIDField(),
        'network_id': obj_fields.UUIDField(),
        'ip_address': obj_fields.IPAddressField(),
    }

    primary_keys = ['subnet_id', 'network_id', 'ip_address']

    foreign_keys = {
        'Port': {'port_id': 'id'},
    }

    # TODO(rossella_s): get rid of it once we switch the db model to using
    # custom types.
    @classmethod
    def modify_fields_to_db(cls, fields):
        result = super(IPAllocation, cls).modify_fields_to_db(fields)
        if 'ip_address' in result:
            result['ip_address'] = cls.filter_to_str(result['ip_address'])
        return result

    # TODO(rossella_s): get rid of it once we switch the db model to using
    # custom types.
    @classmethod
    def modify_fields_from_db(cls, db_obj):
        fields = super(IPAllocation, cls).modify_fields_from_db(db_obj)
        if 'ip_address' in fields:
            fields['ip_address'] = netaddr.IPAddress(fields['ip_address'])
        return fields


@obj_base.VersionedObjectRegistry.register
class PortDNS(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = dns_models.PortDNS

    primary_keys = ['port_id']

    foreign_keys = {
        'Port': {'port_id': 'id'},
    }

    fields = {
        'port_id': obj_fields.UUIDField(),
        'current_dns_name': common_types.DomainNameField(),
        'current_dns_domain': common_types.DomainNameField(),
        'previous_dns_name': common_types.DomainNameField(),
        'previous_dns_domain': common_types.DomainNameField(),
        'dns_name': common_types.DomainNameField(),
    }


@obj_base.VersionedObjectRegistry.register
class Port(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    db_model = models_v2.Port

    fields = {
        'id': obj_fields.UUIDField(),
        'project_id': obj_fields.StringField(nullable=True),
        'name': obj_fields.StringField(nullable=True),
        'network_id': obj_fields.UUIDField(),
        'mac_address': common_types.MACAddressField(),
        'admin_state_up': obj_fields.BooleanField(),
        'device_id': obj_fields.StringField(),
        'device_owner': obj_fields.StringField(),
        'status': obj_fields.StringField(),

        'allowed_address_pairs': obj_fields.ListOfObjectsField(
            'AllowedAddressPair', nullable=True
        ),
        'binding': obj_fields.ObjectField(
            'PortBinding', nullable=True
        ),
        'dhcp_options': obj_fields.ListOfObjectsField(
            'ExtraDhcpOpt', nullable=True
        ),
        'distributed_binding': obj_fields.ObjectField(
            'DistributedPortBinding', nullable=True
        ),
        'dns': obj_fields.ObjectField('PortDNS', nullable=True),
        'fixed_ips': obj_fields.ListOfObjectsField(
            'IPAllocation', nullable=True
        ),
        # TODO(ihrachys): consider converting to boolean
        'security': obj_fields.ObjectField(
            'PortSecurity', nullable=True
        ),
        'security_group_ids': common_types.SetOfUUIDsField(
            nullable=True,
            # TODO(ihrachys): how do we safely pass a mutable default?
            default=None,
        ),
        'qos_policy_id': obj_fields.UUIDField(nullable=True, default=None),

        'binding_levels': obj_fields.ListOfObjectsField(
            'PortBindingLevel', nullable=True
        ),

        # TODO(ihrachys): consider adding a 'dns_assignment' fully synthetic
        # field in later object iterations
    }

    synthetic_fields = [
        'allowed_address_pairs',
        'binding',
        'binding_levels',
        'dhcp_options',
        'distributed_binding',
        'dns',
        'fixed_ips',
        'qos_policy_id',
        'security',
        'security_group_ids',
    ]

    fields_need_translation = {
        'binding': 'port_binding',
        'dhcp_options': 'dhcp_opts',
        'distributed_binding': 'distributed_port_binding',
        'security': 'port_security',
    }

    def create(self):
        fields = self.obj_get_changes()
        with db_api.autonested_transaction(self.obj_context.session):
            sg_ids = self.security_group_ids
            if sg_ids is None:
                sg_ids = set()
            qos_policy_id = self.qos_policy_id
            super(Port, self).create()
            if 'security_group_ids' in fields:
                self._attach_security_groups(sg_ids)
            if 'qos_policy_id' in fields:
                self._attach_qos_policy(qos_policy_id)

    def update(self):
        fields = self.obj_get_changes()
        with db_api.autonested_transaction(self.obj_context.session):
            super(Port, self).update()
            if 'security_group_ids' in fields:
                self._attach_security_groups(fields['security_group_ids'])
            if 'qos_policy_id' in fields:
                self._attach_qos_policy(fields['qos_policy_id'])

    def _attach_qos_policy(self, qos_policy_id):
        # TODO(ihrachys): introduce an object for the binding to isolate
        # database access in a single place, currently scattered between port
        # and policy objects
        obj_db_api.delete_objects(
            self.obj_context, qos_models.QosPortPolicyBinding, port_id=self.id)
        if qos_policy_id:
            obj_db_api.create_object(
                self.obj_context, qos_models.QosPortPolicyBinding,
                {'port_id': self.id, 'policy_id': qos_policy_id}
            )
        self.qos_policy_id = qos_policy_id
        self.obj_reset_changes(['qos_policy_id'])

    def _attach_security_groups(self, sg_ids):
        # TODO(ihrachys): consider introducing an (internal) object for the
        # binding to decouple database operations a bit more
        obj_db_api.delete_objects(
            self.obj_context, sg_models.SecurityGroupPortBinding,
            port_id=self.id,
        )
        if sg_ids:
            for sg_id in sg_ids:
                self._attach_security_group(sg_id)
        self.security_group_ids = sg_ids
        self.obj_reset_changes(['security_group_ids'])

    def _attach_security_group(self, sg_id):
        obj_db_api.create_object(
            self.obj_context, sg_models.SecurityGroupPortBinding,
            {'port_id': self.id, 'security_group_id': sg_id}
        )

    # TODO(rossella_s): get rid of it once we switch the db model to using
    # custom types.
    @classmethod
    def modify_fields_to_db(cls, fields):
        result = super(Port, cls).modify_fields_to_db(fields)
        if 'mac_address' in result:
            result['mac_address'] = cls.filter_to_str(result['mac_address'])
        return result

    # TODO(rossella_s): get rid of it once we switch the db model to using
    # custom types.
    @classmethod
    def modify_fields_from_db(cls, db_obj):
        fields = super(Port, cls).modify_fields_from_db(db_obj)
        if 'mac_address' in fields:
            fields['mac_address'] = utils.AuthenticEUI(fields['mac_address'])
        distributed_port_binding = fields.get('distributed_binding')
        if distributed_port_binding:
            fields['distributed_binding'] = fields['distributed_binding'][0]
        else:
            fields['distributed_binding'] = None
        return fields

    def from_db_object(self, db_obj):
        super(Port, self).from_db_object(db_obj)
        # extract security group bindings
        if db_obj.get('security_groups', []):
            self.security_group_ids = {
                sg.security_group_id
                for sg in db_obj.security_groups
            }
        else:
            self.security_group_ids = set()
        self.obj_reset_changes(['security_group_ids'])

        # extract qos policy binding
        if db_obj.get('qos_policy_binding'):
            self.qos_policy_id = (
                db_obj.qos_policy_binding.policy_id
            )
        else:
            self.qos_policy_id = None
        self.obj_reset_changes(['qos_policy_id'])
