# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chromite/api/image.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from chromite.api.gen.chromite.api import build_api_pb2 as chromite_dot_api_dot_build__api__pb2
from chromite.api.gen.chromite.api import sysroot_pb2 as chromite_dot_api_dot_sysroot__pb2
from chromite.api.gen.chromiumos import common_pb2 as chromiumos_dot_common__pb2
from chromite.api.gen.chromiumos import metrics_pb2 as chromiumos_dot_metrics__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='chromite/api/image.proto',
  package='chromite.api',
  syntax='proto3',
  serialized_options=_b('Z6go.chromium.org/chromiumos/infra/proto/go/chromite/api'),
  serialized_pb=_b('\n\x18\x63hromite/api/image.proto\x12\x0c\x63hromite.api\x1a\x1c\x63hromite/api/build_api.proto\x1a\x1a\x63hromite/api/sysroot.proto\x1a\x17\x63hromiumos/common.proto\x1a\x18\x63hromiumos/metrics.proto\"i\n\x05Image\x12\x0c\n\x04path\x18\x01 \x01(\t\x12#\n\x04type\x18\x02 \x01(\x0e\x32\x15.chromiumos.ImageType\x12-\n\x0c\x62uild_target\x18\x03 \x01(\x0b\x32\x17.chromiumos.BuildTarget\"\xf4\x01\n\x12\x43reateImageRequest\x12-\n\x0c\x62uild_target\x18\x01 \x01(\x0b\x32\x17.chromiumos.BuildTarget\x12*\n\x0bimage_types\x18\x02 \x03(\x0e\x32\x15.chromiumos.ImageType\x12#\n\x1b\x64isable_rootfs_verification\x18\x03 \x01(\x08\x12\x0f\n\x07version\x18\x04 \x01(\t\x12\x13\n\x0b\x64isk_layout\x18\x05 \x01(\t\x12\x14\n\x0c\x62uilder_path\x18\x06 \x01(\t\x12\"\n\x06\x63hroot\x18\x07 \x01(\x0b\x32\x12.chromiumos.Chroot\"\xa4\x01\n\x11\x43reateImageResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12#\n\x06images\x18\x02 \x03(\x0b\x32\x13.chromite.api.Image\x12\x30\n\x0f\x66\x61iled_packages\x18\x03 \x03(\x0b\x32\x17.chromiumos.PackageInfo\x12\'\n\x06\x65vents\x18\x04 \x03(\x0b\x32\x17.chromiumos.MetricEvent\"\xdd\x01\n\x10TestImageRequest\x12\"\n\x05image\x18\x01 \x01(\x0b\x32\x13.chromite.api.Image\x12-\n\x0c\x62uild_target\x18\x02 \x01(\x0b\x32\x17.chromiumos.BuildTarget\x12\x35\n\x06result\x18\x03 \x01(\x0b\x32%.chromite.api.TestImageRequest.Result\x12\"\n\x06\x63hroot\x18\x04 \x01(\x0b\x32\x12.chromiumos.Chroot\x1a\x1b\n\x06Result\x12\x11\n\tdirectory\x18\x01 \x01(\t\"\"\n\x0fTestImageResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\xea\x01\n\x10PushImageRequest\x12\"\n\x06\x63hroot\x18\x01 \x01(\x0b\x32\x12.chromiumos.Chroot\x12\x0e\n\x06\x64ryrun\x18\x02 \x01(\x08\x12\x14\n\x0cgs_image_dir\x18\x03 \x01(\t\x12&\n\x07sysroot\x18\x04 \x01(\x0b\x32\x15.chromite.api.Sysroot\x12$\n\x07profile\x18\x05 \x01(\x0b\x32\x13.chromiumos.Profile\x12)\n\nsign_types\x18\x06 \x03(\x0e\x32\x15.chromiumos.ImageType\x12\x13\n\x0b\x64\x65st_bucket\x18\x07 \x01(\t\"\x13\n\x11PushImageResponse2\xcc\x02\n\x0cImageService\x12K\n\x06\x43reate\x12 .chromite.api.CreateImageRequest\x1a\x1f.chromite.api.CreateImageResult\x12\x45\n\x04Test\x12\x1e.chromite.api.TestImageRequest\x1a\x1d.chromite.api.TestImageResult\x12K\n\nSignerTest\x12\x1e.chromite.api.TestImageRequest\x1a\x1d.chromite.api.TestImageResult\x12L\n\tPushImage\x12\x1e.chromite.api.PushImageRequest\x1a\x1f.chromite.api.PushImageResponse\x1a\r\xc2\xed\x1a\t\n\x05image\x10\x01\x42\x38Z6go.chromium.org/chromiumos/infra/proto/go/chromite/apib\x06proto3')
  ,
  dependencies=[chromite_dot_api_dot_build__api__pb2.DESCRIPTOR,chromite_dot_api_dot_sysroot__pb2.DESCRIPTOR,chromiumos_dot_common__pb2.DESCRIPTOR,chromiumos_dot_metrics__pb2.DESCRIPTOR,])




_IMAGE = _descriptor.Descriptor(
  name='Image',
  full_name='chromite.api.Image',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='path', full_name='chromite.api.Image.path', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='type', full_name='chromite.api.Image.type', index=1,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='build_target', full_name='chromite.api.Image.build_target', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
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
  serialized_start=151,
  serialized_end=256,
)


_CREATEIMAGEREQUEST = _descriptor.Descriptor(
  name='CreateImageRequest',
  full_name='chromite.api.CreateImageRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='build_target', full_name='chromite.api.CreateImageRequest.build_target', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='image_types', full_name='chromite.api.CreateImageRequest.image_types', index=1,
      number=2, type=14, cpp_type=8, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='disable_rootfs_verification', full_name='chromite.api.CreateImageRequest.disable_rootfs_verification', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='version', full_name='chromite.api.CreateImageRequest.version', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='disk_layout', full_name='chromite.api.CreateImageRequest.disk_layout', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='builder_path', full_name='chromite.api.CreateImageRequest.builder_path', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='chroot', full_name='chromite.api.CreateImageRequest.chroot', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
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
  serialized_start=259,
  serialized_end=503,
)


_CREATEIMAGERESULT = _descriptor.Descriptor(
  name='CreateImageResult',
  full_name='chromite.api.CreateImageResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='success', full_name='chromite.api.CreateImageResult.success', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='images', full_name='chromite.api.CreateImageResult.images', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='failed_packages', full_name='chromite.api.CreateImageResult.failed_packages', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='events', full_name='chromite.api.CreateImageResult.events', index=3,
      number=4, type=11, cpp_type=10, label=3,
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
  serialized_start=506,
  serialized_end=670,
)


_TESTIMAGEREQUEST_RESULT = _descriptor.Descriptor(
  name='Result',
  full_name='chromite.api.TestImageRequest.Result',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='directory', full_name='chromite.api.TestImageRequest.Result.directory', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
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
  serialized_start=867,
  serialized_end=894,
)

_TESTIMAGEREQUEST = _descriptor.Descriptor(
  name='TestImageRequest',
  full_name='chromite.api.TestImageRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='image', full_name='chromite.api.TestImageRequest.image', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='build_target', full_name='chromite.api.TestImageRequest.build_target', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='result', full_name='chromite.api.TestImageRequest.result', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='chroot', full_name='chromite.api.TestImageRequest.chroot', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_TESTIMAGEREQUEST_RESULT, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=673,
  serialized_end=894,
)


_TESTIMAGERESULT = _descriptor.Descriptor(
  name='TestImageResult',
  full_name='chromite.api.TestImageResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='success', full_name='chromite.api.TestImageResult.success', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
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
  serialized_start=896,
  serialized_end=930,
)


_PUSHIMAGEREQUEST = _descriptor.Descriptor(
  name='PushImageRequest',
  full_name='chromite.api.PushImageRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='chroot', full_name='chromite.api.PushImageRequest.chroot', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dryrun', full_name='chromite.api.PushImageRequest.dryrun', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='gs_image_dir', full_name='chromite.api.PushImageRequest.gs_image_dir', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sysroot', full_name='chromite.api.PushImageRequest.sysroot', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='profile', full_name='chromite.api.PushImageRequest.profile', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sign_types', full_name='chromite.api.PushImageRequest.sign_types', index=5,
      number=6, type=14, cpp_type=8, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='dest_bucket', full_name='chromite.api.PushImageRequest.dest_bucket', index=6,
      number=7, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
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
  serialized_start=933,
  serialized_end=1167,
)


_PUSHIMAGERESPONSE = _descriptor.Descriptor(
  name='PushImageResponse',
  full_name='chromite.api.PushImageResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
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
  serialized_start=1169,
  serialized_end=1188,
)

_IMAGE.fields_by_name['type'].enum_type = chromiumos_dot_common__pb2._IMAGETYPE
_IMAGE.fields_by_name['build_target'].message_type = chromiumos_dot_common__pb2._BUILDTARGET
_CREATEIMAGEREQUEST.fields_by_name['build_target'].message_type = chromiumos_dot_common__pb2._BUILDTARGET
_CREATEIMAGEREQUEST.fields_by_name['image_types'].enum_type = chromiumos_dot_common__pb2._IMAGETYPE
_CREATEIMAGEREQUEST.fields_by_name['chroot'].message_type = chromiumos_dot_common__pb2._CHROOT
_CREATEIMAGERESULT.fields_by_name['images'].message_type = _IMAGE
_CREATEIMAGERESULT.fields_by_name['failed_packages'].message_type = chromiumos_dot_common__pb2._PACKAGEINFO
_CREATEIMAGERESULT.fields_by_name['events'].message_type = chromiumos_dot_metrics__pb2._METRICEVENT
_TESTIMAGEREQUEST_RESULT.containing_type = _TESTIMAGEREQUEST
_TESTIMAGEREQUEST.fields_by_name['image'].message_type = _IMAGE
_TESTIMAGEREQUEST.fields_by_name['build_target'].message_type = chromiumos_dot_common__pb2._BUILDTARGET
_TESTIMAGEREQUEST.fields_by_name['result'].message_type = _TESTIMAGEREQUEST_RESULT
_TESTIMAGEREQUEST.fields_by_name['chroot'].message_type = chromiumos_dot_common__pb2._CHROOT
_PUSHIMAGEREQUEST.fields_by_name['chroot'].message_type = chromiumos_dot_common__pb2._CHROOT
_PUSHIMAGEREQUEST.fields_by_name['sysroot'].message_type = chromite_dot_api_dot_sysroot__pb2._SYSROOT
_PUSHIMAGEREQUEST.fields_by_name['profile'].message_type = chromiumos_dot_common__pb2._PROFILE
_PUSHIMAGEREQUEST.fields_by_name['sign_types'].enum_type = chromiumos_dot_common__pb2._IMAGETYPE
DESCRIPTOR.message_types_by_name['Image'] = _IMAGE
DESCRIPTOR.message_types_by_name['CreateImageRequest'] = _CREATEIMAGEREQUEST
DESCRIPTOR.message_types_by_name['CreateImageResult'] = _CREATEIMAGERESULT
DESCRIPTOR.message_types_by_name['TestImageRequest'] = _TESTIMAGEREQUEST
DESCRIPTOR.message_types_by_name['TestImageResult'] = _TESTIMAGERESULT
DESCRIPTOR.message_types_by_name['PushImageRequest'] = _PUSHIMAGEREQUEST
DESCRIPTOR.message_types_by_name['PushImageResponse'] = _PUSHIMAGERESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Image = _reflection.GeneratedProtocolMessageType('Image', (_message.Message,), dict(
  DESCRIPTOR = _IMAGE,
  __module__ = 'chromite.api.image_pb2'
  # @@protoc_insertion_point(class_scope:chromite.api.Image)
  ))
_sym_db.RegisterMessage(Image)

CreateImageRequest = _reflection.GeneratedProtocolMessageType('CreateImageRequest', (_message.Message,), dict(
  DESCRIPTOR = _CREATEIMAGEREQUEST,
  __module__ = 'chromite.api.image_pb2'
  # @@protoc_insertion_point(class_scope:chromite.api.CreateImageRequest)
  ))
_sym_db.RegisterMessage(CreateImageRequest)

CreateImageResult = _reflection.GeneratedProtocolMessageType('CreateImageResult', (_message.Message,), dict(
  DESCRIPTOR = _CREATEIMAGERESULT,
  __module__ = 'chromite.api.image_pb2'
  # @@protoc_insertion_point(class_scope:chromite.api.CreateImageResult)
  ))
_sym_db.RegisterMessage(CreateImageResult)

TestImageRequest = _reflection.GeneratedProtocolMessageType('TestImageRequest', (_message.Message,), dict(

  Result = _reflection.GeneratedProtocolMessageType('Result', (_message.Message,), dict(
    DESCRIPTOR = _TESTIMAGEREQUEST_RESULT,
    __module__ = 'chromite.api.image_pb2'
    # @@protoc_insertion_point(class_scope:chromite.api.TestImageRequest.Result)
    ))
  ,
  DESCRIPTOR = _TESTIMAGEREQUEST,
  __module__ = 'chromite.api.image_pb2'
  # @@protoc_insertion_point(class_scope:chromite.api.TestImageRequest)
  ))
_sym_db.RegisterMessage(TestImageRequest)
_sym_db.RegisterMessage(TestImageRequest.Result)

TestImageResult = _reflection.GeneratedProtocolMessageType('TestImageResult', (_message.Message,), dict(
  DESCRIPTOR = _TESTIMAGERESULT,
  __module__ = 'chromite.api.image_pb2'
  # @@protoc_insertion_point(class_scope:chromite.api.TestImageResult)
  ))
_sym_db.RegisterMessage(TestImageResult)

PushImageRequest = _reflection.GeneratedProtocolMessageType('PushImageRequest', (_message.Message,), dict(
  DESCRIPTOR = _PUSHIMAGEREQUEST,
  __module__ = 'chromite.api.image_pb2'
  # @@protoc_insertion_point(class_scope:chromite.api.PushImageRequest)
  ))
_sym_db.RegisterMessage(PushImageRequest)

PushImageResponse = _reflection.GeneratedProtocolMessageType('PushImageResponse', (_message.Message,), dict(
  DESCRIPTOR = _PUSHIMAGERESPONSE,
  __module__ = 'chromite.api.image_pb2'
  # @@protoc_insertion_point(class_scope:chromite.api.PushImageResponse)
  ))
_sym_db.RegisterMessage(PushImageResponse)


DESCRIPTOR._options = None

_IMAGESERVICE = _descriptor.ServiceDescriptor(
  name='ImageService',
  full_name='chromite.api.ImageService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=_b('\302\355\032\t\n\005image\020\001'),
  serialized_start=1191,
  serialized_end=1523,
  methods=[
  _descriptor.MethodDescriptor(
    name='Create',
    full_name='chromite.api.ImageService.Create',
    index=0,
    containing_service=None,
    input_type=_CREATEIMAGEREQUEST,
    output_type=_CREATEIMAGERESULT,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='Test',
    full_name='chromite.api.ImageService.Test',
    index=1,
    containing_service=None,
    input_type=_TESTIMAGEREQUEST,
    output_type=_TESTIMAGERESULT,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='SignerTest',
    full_name='chromite.api.ImageService.SignerTest',
    index=2,
    containing_service=None,
    input_type=_TESTIMAGEREQUEST,
    output_type=_TESTIMAGERESULT,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='PushImage',
    full_name='chromite.api.ImageService.PushImage',
    index=3,
    containing_service=None,
    input_type=_PUSHIMAGEREQUEST,
    output_type=_PUSHIMAGERESPONSE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_IMAGESERVICE)

DESCRIPTOR.services_by_name['ImageService'] = _IMAGESERVICE

# @@protoc_insertion_point(module_scope)
