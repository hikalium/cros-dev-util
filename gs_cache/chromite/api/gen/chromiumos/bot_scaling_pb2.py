# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chromiumos/bot_scaling.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='chromiumos/bot_scaling.proto',
  package='chromiumos',
  syntax='proto3',
  serialized_options=_b('Z4go.chromium.org/chromiumos/infra/proto/go/chromiumos'),
  serialized_pb=_b('\n\x1c\x63hromiumos/bot_scaling.proto\x12\nchromiumos\"Z\n\x07\x42otType\x12\x10\n\x08\x62ot_size\x18\x01 \x01(\t\x12\x15\n\rcores_per_bot\x18\x02 \x01(\x02\x12\x13\n\x0bhourly_cost\x18\x03 \x01(\x02\x12\x11\n\tmemory_gb\x18\x04 \x01(\x02\"@\n\x11SwarmingDimension\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\x12\x0e\n\x06values\x18\x03 \x03(\t\"\x95\x06\n\tBotPolicy\x12\x11\n\tbot_group\x18\x01 \x01(\t\x12%\n\x08\x62ot_type\x18\x02 \x01(\x0b\x32\x13.chromiumos.BotType\x12\x45\n\x13scaling_restriction\x18\x03 \x01(\x0b\x32(.chromiumos.BotPolicy.ScalingRestriction\x12\x44\n\x13region_restrictions\x18\x04 \x03(\x0b\x32\'.chromiumos.BotPolicy.RegionRestriction\x12:\n\x13swarming_dimensions\x18\x05 \x03(\x0b\x32\x1d.chromiumos.SwarmingDimension\x12/\n\x0bpolicy_mode\x18\x06 \x01(\x0e\x32\x1a.chromiumos.BotPolicy.Mode\x12\x16\n\x0elookback_hours\x18\x07 \x01(\x11\x12:\n\x0cscaling_mode\x18\x08 \x01(\x0e\x32$.chromiumos.BotPolicy.BotScalingMode\x12\x19\n\x11swarming_instance\x18\t \x01(\t\x12\x13\n\x0b\x61pplication\x18\n \x01(\t\x1aw\n\x12ScalingRestriction\x12\x13\n\x0b\x62ot_ceiling\x18\x01 \x01(\x05\x12\x11\n\tbot_floor\x18\x02 \x01(\x05\x12\x10\n\x08min_idle\x18\x03 \x01(\x05\x12\x11\n\tstep_size\x18\x04 \x01(\x05\x12\x14\n\x0c\x62ot_fallback\x18\x05 \x01(\x05\x1a\x43\n\x11RegionRestriction\x12\x0e\n\x06region\x18\x01 \x01(\t\x12\x0e\n\x06prefix\x18\x02 \x01(\t\x12\x0e\n\x06weight\x18\x03 \x01(\x02\"7\n\x04Mode\x12\x10\n\x0cUNKNOWN_MODE\x10\x00\x12\r\n\tMONITORED\x10\x01\x12\x0e\n\nCONFIGURED\x10\x02\"Y\n\x0e\x42otScalingMode\x12\x18\n\x14UNKNOWN_SCALING_MODE\x10\x00\x12\x0b\n\x07STEPPED\x10\x01\x12\n\n\x06\x44\x45MAND\x10\x02\x12\x14\n\x10STEPPED_DECREASE\x10\x03\";\n\x0c\x42otPolicyCfg\x12+\n\x0c\x62ot_policies\x18\x01 \x03(\x0b\x32\x15.chromiumos.BotPolicy\"}\n\x10ReducedBotPolicy\x12\x11\n\tbot_group\x18\x01 \x01(\t\x12%\n\x08\x62ot_type\x18\x02 \x01(\x0b\x32\x13.chromiumos.BotType\x12/\n\x0bpolicy_mode\x18\x03 \x01(\x0e\x32\x1a.chromiumos.BotPolicy.Mode\"I\n\x13ReducedBotPolicyCfg\x12\x32\n\x0c\x62ot_policies\x18\x01 \x03(\x0b\x32\x1c.chromiumos.ReducedBotPolicy\"\xab\x03\n\rScalingAction\x12\x11\n\tbot_group\x18\x01 \x01(\t\x12%\n\x08\x62ot_type\x18\x02 \x01(\x0b\x32\x13.chromiumos.BotType\x12\x38\n\nactionable\x18\x03 \x01(\x0e\x32$.chromiumos.ScalingAction.Actionable\x12\x16\n\x0e\x62ots_requested\x18\x04 \x01(\x05\x12\x42\n\x10regional_actions\x18\x05 \x03(\x0b\x32(.chromiumos.ScalingAction.RegionalAction\x12\x19\n\x11\x65stimated_savings\x18\x06 \x01(\x02\x12\x0f\n\x07\x62ot_min\x18\x07 \x01(\x05\x12\x0f\n\x07\x62ot_max\x18\x08 \x01(\x05\x12\x13\n\x0b\x61pplication\x18\t \x01(\t\x1aH\n\x0eRegionalAction\x12\x0e\n\x06region\x18\x01 \x01(\t\x12\x0e\n\x06prefix\x18\x02 \x01(\t\x12\x16\n\x0e\x62ots_requested\x18\x03 \x01(\x05\".\n\nActionable\x12\x0f\n\x0bUNSPECIFIED\x10\x00\x12\x07\n\x03YES\x10\x01\x12\x06\n\x02NO\x10\x02\"v\n\x13ResourceUtilization\x12\x0e\n\x06region\x18\x01 \x01(\t\x12\x0b\n\x03vms\x18\x02 \x01(\x05\x12\x0c\n\x04\x63pus\x18\x03 \x01(\x02\x12\x11\n\tmemory_gb\x18\x04 \x01(\x02\x12\x0f\n\x07\x64isk_gb\x18\x05 \x01(\x02\x12\x10\n\x08max_cpus\x18\x06 \x01(\x02\"l\n\x16\x41pplicationUtilization\x12\x13\n\x0b\x61pplication\x18\x01 \x01(\t\x12=\n\x14resource_utilization\x18\x02 \x03(\x0b\x32\x1f.chromiumos.ResourceUtilization\"\xca\x01\n\x0eRoboCropAction\x12\x32\n\x0fscaling_actions\x18\x01 \x03(\x0b\x32\x19.chromiumos.ScalingAction\x12=\n\x14resource_utilization\x18\x02 \x03(\x0b\x32\x1f.chromiumos.ResourceUtilization\x12\x45\n\x19\x61ppl_resource_utilization\x18\x03 \x03(\x0b\x32\".chromiumos.ApplicationUtilizationB6Z4go.chromium.org/chromiumos/infra/proto/go/chromiumosb\x06proto3')
)



_BOTPOLICY_MODE = _descriptor.EnumDescriptor(
  name='Mode',
  full_name='chromiumos.BotPolicy.Mode',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='UNKNOWN_MODE', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='MONITORED', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CONFIGURED', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=846,
  serialized_end=901,
)
_sym_db.RegisterEnumDescriptor(_BOTPOLICY_MODE)

_BOTPOLICY_BOTSCALINGMODE = _descriptor.EnumDescriptor(
  name='BotScalingMode',
  full_name='chromiumos.BotPolicy.BotScalingMode',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='UNKNOWN_SCALING_MODE', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='STEPPED', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DEMAND', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='STEPPED_DECREASE', index=3, number=3,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=903,
  serialized_end=992,
)
_sym_db.RegisterEnumDescriptor(_BOTPOLICY_BOTSCALINGMODE)

_SCALINGACTION_ACTIONABLE = _descriptor.EnumDescriptor(
  name='Actionable',
  full_name='chromiumos.ScalingAction.Actionable',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='UNSPECIFIED', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='YES', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='NO', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1639,
  serialized_end=1685,
)
_sym_db.RegisterEnumDescriptor(_SCALINGACTION_ACTIONABLE)


_BOTTYPE = _descriptor.Descriptor(
  name='BotType',
  full_name='chromiumos.BotType',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bot_size', full_name='chromiumos.BotType.bot_size', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='cores_per_bot', full_name='chromiumos.BotType.cores_per_bot', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='hourly_cost', full_name='chromiumos.BotType.hourly_cost', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='memory_gb', full_name='chromiumos.BotType.memory_gb', index=3,
      number=4, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=44,
  serialized_end=134,
)


_SWARMINGDIMENSION = _descriptor.Descriptor(
  name='SwarmingDimension',
  full_name='chromiumos.SwarmingDimension',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='chromiumos.SwarmingDimension.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='chromiumos.SwarmingDimension.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='values', full_name='chromiumos.SwarmingDimension.values', index=2,
      number=3, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=136,
  serialized_end=200,
)


_BOTPOLICY_SCALINGRESTRICTION = _descriptor.Descriptor(
  name='ScalingRestriction',
  full_name='chromiumos.BotPolicy.ScalingRestriction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bot_ceiling', full_name='chromiumos.BotPolicy.ScalingRestriction.bot_ceiling', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bot_floor', full_name='chromiumos.BotPolicy.ScalingRestriction.bot_floor', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='min_idle', full_name='chromiumos.BotPolicy.ScalingRestriction.min_idle', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='step_size', full_name='chromiumos.BotPolicy.ScalingRestriction.step_size', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bot_fallback', full_name='chromiumos.BotPolicy.ScalingRestriction.bot_fallback', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=656,
  serialized_end=775,
)

_BOTPOLICY_REGIONRESTRICTION = _descriptor.Descriptor(
  name='RegionRestriction',
  full_name='chromiumos.BotPolicy.RegionRestriction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='region', full_name='chromiumos.BotPolicy.RegionRestriction.region', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='prefix', full_name='chromiumos.BotPolicy.RegionRestriction.prefix', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='weight', full_name='chromiumos.BotPolicy.RegionRestriction.weight', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=777,
  serialized_end=844,
)

_BOTPOLICY = _descriptor.Descriptor(
  name='BotPolicy',
  full_name='chromiumos.BotPolicy',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bot_group', full_name='chromiumos.BotPolicy.bot_group', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bot_type', full_name='chromiumos.BotPolicy.bot_type', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='scaling_restriction', full_name='chromiumos.BotPolicy.scaling_restriction', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='region_restrictions', full_name='chromiumos.BotPolicy.region_restrictions', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='swarming_dimensions', full_name='chromiumos.BotPolicy.swarming_dimensions', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='policy_mode', full_name='chromiumos.BotPolicy.policy_mode', index=5,
      number=6, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='lookback_hours', full_name='chromiumos.BotPolicy.lookback_hours', index=6,
      number=7, type=17, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='scaling_mode', full_name='chromiumos.BotPolicy.scaling_mode', index=7,
      number=8, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='swarming_instance', full_name='chromiumos.BotPolicy.swarming_instance', index=8,
      number=9, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='application', full_name='chromiumos.BotPolicy.application', index=9,
      number=10, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_BOTPOLICY_SCALINGRESTRICTION, _BOTPOLICY_REGIONRESTRICTION, ],
  enum_types=[
    _BOTPOLICY_MODE,
    _BOTPOLICY_BOTSCALINGMODE,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=203,
  serialized_end=992,
)


_BOTPOLICYCFG = _descriptor.Descriptor(
  name='BotPolicyCfg',
  full_name='chromiumos.BotPolicyCfg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bot_policies', full_name='chromiumos.BotPolicyCfg.bot_policies', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=994,
  serialized_end=1053,
)


_REDUCEDBOTPOLICY = _descriptor.Descriptor(
  name='ReducedBotPolicy',
  full_name='chromiumos.ReducedBotPolicy',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bot_group', full_name='chromiumos.ReducedBotPolicy.bot_group', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bot_type', full_name='chromiumos.ReducedBotPolicy.bot_type', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='policy_mode', full_name='chromiumos.ReducedBotPolicy.policy_mode', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1055,
  serialized_end=1180,
)


_REDUCEDBOTPOLICYCFG = _descriptor.Descriptor(
  name='ReducedBotPolicyCfg',
  full_name='chromiumos.ReducedBotPolicyCfg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bot_policies', full_name='chromiumos.ReducedBotPolicyCfg.bot_policies', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1182,
  serialized_end=1255,
)


_SCALINGACTION_REGIONALACTION = _descriptor.Descriptor(
  name='RegionalAction',
  full_name='chromiumos.ScalingAction.RegionalAction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='region', full_name='chromiumos.ScalingAction.RegionalAction.region', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='prefix', full_name='chromiumos.ScalingAction.RegionalAction.prefix', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bots_requested', full_name='chromiumos.ScalingAction.RegionalAction.bots_requested', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1565,
  serialized_end=1637,
)

_SCALINGACTION = _descriptor.Descriptor(
  name='ScalingAction',
  full_name='chromiumos.ScalingAction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bot_group', full_name='chromiumos.ScalingAction.bot_group', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bot_type', full_name='chromiumos.ScalingAction.bot_type', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='actionable', full_name='chromiumos.ScalingAction.actionable', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bots_requested', full_name='chromiumos.ScalingAction.bots_requested', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='regional_actions', full_name='chromiumos.ScalingAction.regional_actions', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='estimated_savings', full_name='chromiumos.ScalingAction.estimated_savings', index=5,
      number=6, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bot_min', full_name='chromiumos.ScalingAction.bot_min', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bot_max', full_name='chromiumos.ScalingAction.bot_max', index=7,
      number=8, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='application', full_name='chromiumos.ScalingAction.application', index=8,
      number=9, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_SCALINGACTION_REGIONALACTION, ],
  enum_types=[
    _SCALINGACTION_ACTIONABLE,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1258,
  serialized_end=1685,
)


_RESOURCEUTILIZATION = _descriptor.Descriptor(
  name='ResourceUtilization',
  full_name='chromiumos.ResourceUtilization',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='region', full_name='chromiumos.ResourceUtilization.region', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='vms', full_name='chromiumos.ResourceUtilization.vms', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='cpus', full_name='chromiumos.ResourceUtilization.cpus', index=2,
      number=3, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='memory_gb', full_name='chromiumos.ResourceUtilization.memory_gb', index=3,
      number=4, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='disk_gb', full_name='chromiumos.ResourceUtilization.disk_gb', index=4,
      number=5, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='max_cpus', full_name='chromiumos.ResourceUtilization.max_cpus', index=5,
      number=6, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1687,
  serialized_end=1805,
)


_APPLICATIONUTILIZATION = _descriptor.Descriptor(
  name='ApplicationUtilization',
  full_name='chromiumos.ApplicationUtilization',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='application', full_name='chromiumos.ApplicationUtilization.application', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='resource_utilization', full_name='chromiumos.ApplicationUtilization.resource_utilization', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1807,
  serialized_end=1915,
)


_ROBOCROPACTION = _descriptor.Descriptor(
  name='RoboCropAction',
  full_name='chromiumos.RoboCropAction',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='scaling_actions', full_name='chromiumos.RoboCropAction.scaling_actions', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='resource_utilization', full_name='chromiumos.RoboCropAction.resource_utilization', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='appl_resource_utilization', full_name='chromiumos.RoboCropAction.appl_resource_utilization', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1918,
  serialized_end=2120,
)

_BOTPOLICY_SCALINGRESTRICTION.containing_type = _BOTPOLICY
_BOTPOLICY_REGIONRESTRICTION.containing_type = _BOTPOLICY
_BOTPOLICY.fields_by_name['bot_type'].message_type = _BOTTYPE
_BOTPOLICY.fields_by_name['scaling_restriction'].message_type = _BOTPOLICY_SCALINGRESTRICTION
_BOTPOLICY.fields_by_name['region_restrictions'].message_type = _BOTPOLICY_REGIONRESTRICTION
_BOTPOLICY.fields_by_name['swarming_dimensions'].message_type = _SWARMINGDIMENSION
_BOTPOLICY.fields_by_name['policy_mode'].enum_type = _BOTPOLICY_MODE
_BOTPOLICY.fields_by_name['scaling_mode'].enum_type = _BOTPOLICY_BOTSCALINGMODE
_BOTPOLICY_MODE.containing_type = _BOTPOLICY
_BOTPOLICY_BOTSCALINGMODE.containing_type = _BOTPOLICY
_BOTPOLICYCFG.fields_by_name['bot_policies'].message_type = _BOTPOLICY
_REDUCEDBOTPOLICY.fields_by_name['bot_type'].message_type = _BOTTYPE
_REDUCEDBOTPOLICY.fields_by_name['policy_mode'].enum_type = _BOTPOLICY_MODE
_REDUCEDBOTPOLICYCFG.fields_by_name['bot_policies'].message_type = _REDUCEDBOTPOLICY
_SCALINGACTION_REGIONALACTION.containing_type = _SCALINGACTION
_SCALINGACTION.fields_by_name['bot_type'].message_type = _BOTTYPE
_SCALINGACTION.fields_by_name['actionable'].enum_type = _SCALINGACTION_ACTIONABLE
_SCALINGACTION.fields_by_name['regional_actions'].message_type = _SCALINGACTION_REGIONALACTION
_SCALINGACTION_ACTIONABLE.containing_type = _SCALINGACTION
_APPLICATIONUTILIZATION.fields_by_name['resource_utilization'].message_type = _RESOURCEUTILIZATION
_ROBOCROPACTION.fields_by_name['scaling_actions'].message_type = _SCALINGACTION
_ROBOCROPACTION.fields_by_name['resource_utilization'].message_type = _RESOURCEUTILIZATION
_ROBOCROPACTION.fields_by_name['appl_resource_utilization'].message_type = _APPLICATIONUTILIZATION
DESCRIPTOR.message_types_by_name['BotType'] = _BOTTYPE
DESCRIPTOR.message_types_by_name['SwarmingDimension'] = _SWARMINGDIMENSION
DESCRIPTOR.message_types_by_name['BotPolicy'] = _BOTPOLICY
DESCRIPTOR.message_types_by_name['BotPolicyCfg'] = _BOTPOLICYCFG
DESCRIPTOR.message_types_by_name['ReducedBotPolicy'] = _REDUCEDBOTPOLICY
DESCRIPTOR.message_types_by_name['ReducedBotPolicyCfg'] = _REDUCEDBOTPOLICYCFG
DESCRIPTOR.message_types_by_name['ScalingAction'] = _SCALINGACTION
DESCRIPTOR.message_types_by_name['ResourceUtilization'] = _RESOURCEUTILIZATION
DESCRIPTOR.message_types_by_name['ApplicationUtilization'] = _APPLICATIONUTILIZATION
DESCRIPTOR.message_types_by_name['RoboCropAction'] = _ROBOCROPACTION
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

BotType = _reflection.GeneratedProtocolMessageType('BotType', (_message.Message,), dict(
  DESCRIPTOR = _BOTTYPE,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.BotType)
  ))
_sym_db.RegisterMessage(BotType)

SwarmingDimension = _reflection.GeneratedProtocolMessageType('SwarmingDimension', (_message.Message,), dict(
  DESCRIPTOR = _SWARMINGDIMENSION,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.SwarmingDimension)
  ))
_sym_db.RegisterMessage(SwarmingDimension)

BotPolicy = _reflection.GeneratedProtocolMessageType('BotPolicy', (_message.Message,), dict(

  ScalingRestriction = _reflection.GeneratedProtocolMessageType('ScalingRestriction', (_message.Message,), dict(
    DESCRIPTOR = _BOTPOLICY_SCALINGRESTRICTION,
    __module__ = 'chromiumos.bot_scaling_pb2'
    # @@protoc_insertion_point(class_scope:chromiumos.BotPolicy.ScalingRestriction)
    ))
  ,

  RegionRestriction = _reflection.GeneratedProtocolMessageType('RegionRestriction', (_message.Message,), dict(
    DESCRIPTOR = _BOTPOLICY_REGIONRESTRICTION,
    __module__ = 'chromiumos.bot_scaling_pb2'
    # @@protoc_insertion_point(class_scope:chromiumos.BotPolicy.RegionRestriction)
    ))
  ,
  DESCRIPTOR = _BOTPOLICY,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.BotPolicy)
  ))
_sym_db.RegisterMessage(BotPolicy)
_sym_db.RegisterMessage(BotPolicy.ScalingRestriction)
_sym_db.RegisterMessage(BotPolicy.RegionRestriction)

BotPolicyCfg = _reflection.GeneratedProtocolMessageType('BotPolicyCfg', (_message.Message,), dict(
  DESCRIPTOR = _BOTPOLICYCFG,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.BotPolicyCfg)
  ))
_sym_db.RegisterMessage(BotPolicyCfg)

ReducedBotPolicy = _reflection.GeneratedProtocolMessageType('ReducedBotPolicy', (_message.Message,), dict(
  DESCRIPTOR = _REDUCEDBOTPOLICY,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.ReducedBotPolicy)
  ))
_sym_db.RegisterMessage(ReducedBotPolicy)

ReducedBotPolicyCfg = _reflection.GeneratedProtocolMessageType('ReducedBotPolicyCfg', (_message.Message,), dict(
  DESCRIPTOR = _REDUCEDBOTPOLICYCFG,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.ReducedBotPolicyCfg)
  ))
_sym_db.RegisterMessage(ReducedBotPolicyCfg)

ScalingAction = _reflection.GeneratedProtocolMessageType('ScalingAction', (_message.Message,), dict(

  RegionalAction = _reflection.GeneratedProtocolMessageType('RegionalAction', (_message.Message,), dict(
    DESCRIPTOR = _SCALINGACTION_REGIONALACTION,
    __module__ = 'chromiumos.bot_scaling_pb2'
    # @@protoc_insertion_point(class_scope:chromiumos.ScalingAction.RegionalAction)
    ))
  ,
  DESCRIPTOR = _SCALINGACTION,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.ScalingAction)
  ))
_sym_db.RegisterMessage(ScalingAction)
_sym_db.RegisterMessage(ScalingAction.RegionalAction)

ResourceUtilization = _reflection.GeneratedProtocolMessageType('ResourceUtilization', (_message.Message,), dict(
  DESCRIPTOR = _RESOURCEUTILIZATION,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.ResourceUtilization)
  ))
_sym_db.RegisterMessage(ResourceUtilization)

ApplicationUtilization = _reflection.GeneratedProtocolMessageType('ApplicationUtilization', (_message.Message,), dict(
  DESCRIPTOR = _APPLICATIONUTILIZATION,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.ApplicationUtilization)
  ))
_sym_db.RegisterMessage(ApplicationUtilization)

RoboCropAction = _reflection.GeneratedProtocolMessageType('RoboCropAction', (_message.Message,), dict(
  DESCRIPTOR = _ROBOCROPACTION,
  __module__ = 'chromiumos.bot_scaling_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.RoboCropAction)
  ))
_sym_db.RegisterMessage(RoboCropAction)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
