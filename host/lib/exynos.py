# Copyright (c) 2013 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This module supports creating Exynos bootprom images"""

import os
import struct

from tools import CmdError

class ExynosBl2(object):
  """Class for processing Exynos SPL2 file.

  Attributes:
    _tools: A tools.Tools object to use for external tools, provided by the
            caller
    _out: A cros_output.Output object to use for console output, provided by
            the caller
  """

  def __init__(self, tools, output):
    """Set up a new object."""
    self._tools = tools
    self._out = output
    self.spl_source = 'straps'  # SPL boot according to board settings

  def _UpdateParameters(self, fdt, spl_load_size, data, pos):
    """Update the parameters in a BL2 blob.

    We look at the list in the parameter block, extract the value of each
    from the device tree, and write that value to the parameter block.

    Args:
      fdt: Device tree containing the parameter values.
      spl_load_size: Size of U-Boot image that SPL must load
      data: The BL2 data.
      pos: The position of the start of the parameter block.

    Returns:
      The new contents of the parameter block, after updating.
    """
    version, size = struct.unpack('<2L', data[pos + 4:pos + 12])
    if version != 1:
      raise CmdError("Cannot update machine parameter block version '%d'" %
          version)
    if size < 0 or pos + size > len(data):
      raise CmdError("Machine parameter block size %d is invalid: "
            "pos=%d, size=%d, space=%d, len=%d" %
            (size, pos, size, len(data) - pos, len(data)))

    # Move past the header and read the parameter list, which is terminated
    # with \0.
    pos += 12
    param_list = struct.unpack('<%ds' % (len(data) - pos), data[pos:])[0]
    param_len = param_list.find('\0')
    param_list = param_list[:param_len]
    pos += (param_len + 4) & ~3

    # Work through the parameters one at a time, adding each value
    new_data = ''
    upto = 0
    for param in param_list:
      value = struct.unpack('<1L', data[pos + upto:pos + upto + 4])[0]

      # Use this to detect a missing value from the fdt.
      not_given = 'not-given-invalid-value'
      if param == 'm' :
        mem_type = fdt.GetString('/dmc', 'mem-type', not_given)
        if mem_type == not_given:
          mem_type = 'ddr3'
          self._out.Warning("No value for memory type: using '%s'" % mem_type)
        mem_types = ['ddr2', 'ddr3', 'lpddr2', 'lpddr3']
        if not mem_type in mem_types:
          raise CmdError("Unknown memory type '%s'" % mem_type)
        value = mem_types.index(mem_type)
        self._out.Info('  Memory type: %s (%d)' % (mem_type, value))
      elif param == 'M' :
        mem_manuf = fdt.GetString('/dmc', 'mem-manuf', not_given)
        if mem_manuf == not_given:
          mem_manuf = 'samsung'
          self._out.Warning("No value for memory manufacturer: using '%s'" %
                            mem_manuf)
        mem_manufs = ['autodetect', 'elpida', 'samsung']
        if not mem_manuf in mem_manufs:
          raise CmdError("Unknown memory manufacturer: '%s'" % mem_manuf)
        value = mem_manufs.index(mem_manuf)
        self._out.Info('  Memory manufacturer: %s (%d)' % (mem_manuf, value))
      elif param == 'f' :
        mem_freq = fdt.GetInt('/dmc', 'clock-frequency', -1)
        if mem_freq == -1:
          mem_freq = 800000000
          self._out.Warning("No value for memory frequency: using '%s'" %
                            mem_freq)
        mem_freq /= 1000000
        if not mem_freq in [533, 667, 800]:
          self._out.Warning("Unexpected memory speed '%s'" % mem_freq)
        value = mem_freq
        self._out.Info('  Memory speed: %d' % mem_freq)
      elif param == 'a' :
        arm_freq = fdt.GetInt('/dmc', 'arm-frequency', -1)
        if arm_freq == -1:
          arm_freq = 1700000000
          self._out.Warning("No value for ARM frequency: using '%s'" %
                            arm_freq)
        arm_freq /= 1000000
        value = arm_freq
        self._out.Info('  ARM speed: %d' % arm_freq)
      elif param == 'i':
        i2c_addr = -1
        lookup = fdt.GetString('/aliases', 'pmic', '')
        if lookup:
          i2c_addr, size = fdt.GetIntList(lookup, 'reg', 2)
        if i2c_addr == -1:
          self._out.Warning("No value for PMIC I2C address: using %#08x" %
                            value)
        else:
          value = i2c_addr
        self._out.Info('  PMIC I2C Address: %#08x' % value)
      elif param == 's':
        serial_addr = -1
        lookup = fdt.GetString('/aliases', 'console', '')
        if lookup:
          serial_addr, size = fdt.GetIntList(lookup, 'reg', 2)
        if serial_addr == -1:
          self._out.Warning("No value for Console address: using %#08x" %
                            value)
        else:
          value = serial_addr
        self._out.Info('  Console Address: %#08x' % value)
      elif param == 'v':
        value = 31
        self._out.Info('  Memory interleave: %#0x' % value)
      elif param == 'u':
        value = (spl_load_size + 0xfff) & ~0xfff
        self._out.Info('  U-Boot size: %#0x (rounded up from %#0x)' %
            (value, spl_load_size))
      elif param == 'l':
        load_addr = fdt.GetInt('/config', 'u-boot-load-addr', -1)
        if load_addr == -1:
          self._out.Warning("No value for U-Boot load address: using '%08x'" %
                            value)
        else:
          value = load_addr
        self._out.Info('  U-Boot load address: %#0x' % value)
      elif param == 'b':
        # These values come from enum boot_mode in U-Boot's cpu.h
        if self.spl_source == 'straps':
          value = 32
        elif self.spl_source == 'emmc':
          value = 4
        elif self.spl_source == 'spi':
          value = 20
        elif self.spl_source == 'usb':
          value = 33
        else:
          raise CmdError("Invalid boot source '%s'" % self.spl_source)
        self._out.Info('  Boot source: %#0x' % value)
      elif param in ['r', 'R']:
        records = fdt.GetIntList('/board-rev', 'google,board-rev-gpios',
                                 None, '0 0')
        gpios = []
        for i in range(1, len(records), 3):
          gpios.append(records[i])
        gpios.extend([0, 0, 0, 0])
        if param == 'r':
          value = gpios[0] + (gpios[1] << 16)
          self._out.Info('  Board ID GPIOs: tit0=%d, tit1=%d' % (gpios[0],
                         gpios[1]))
        else:
          value = gpios[2] + (gpios[3] << 16)
          self._out.Info('  Board ID GPIOs: tit2=%d, tit3=%d' % (gpios[2],
                         gpios[3]))
      elif param == 'z':
        compress = fdt.GetString('/flash/ro-boot', 'compress', 'none')
        compress_types = ['none', 'lzo']
        if not compress in compress_types:
          raise CmdError("Unknown compression type '%s'" % compress)
        value = compress_types.index(compress)
        self._out.Info('  Compression type: %#0x' % value)
      elif param == 'c':
        rtc_type = 0
        try:
          rtc_alias = fdt.GetString('/aliases/', 'rtc')
          rtc_compat = fdt.GetString(rtc_alias, 'compatible')
          if rtc_compat == 'samsung,s5m8767-pmic':
            rtc_type = 1
        except CmdError:
          self._out.Warning("Failed to find rtc")
        value = rtc_type
      else:
        self._out.Warning("Unknown machine parameter type '%s'" % param)
        self._out.Info('  Unknown value: %#0x' % value)
      new_data += struct.pack('<L', value)
      upto += 4

    # Put the data into our block.
    data = data[:pos] + new_data + data[pos + len(new_data):]
    self._out.Info('BL2 configuration complete')
    return data

  def _UpdateChecksum(self, data):
    """Update the BL2 checksum.

    The checksum is a 4 byte sum of all the bytes in the image before the
    last 4 bytes (which hold the checksum).

    Args:
      data: The BL2 data to update.

    Returns:
      The new contents of the BL2 data, after updating the checksum.
    """
    checksum = 0
    for ch in data[:-4]:
      checksum += ord(ch)
    return data[:-4] + struct.pack('<L', checksum & 0xffffffff)

  def Configure(self, fdt, spl_load_size, orig_bl2, name=''):
    """Configure an Exynos BL2 binary for our needs.

    We create a new modified BL2 and return its filename.

    Args:
      fdt: Device tree containing the parameter values.
      spl_load_size: Size of U-Boot image that SPL must load
      orig_bl2: Filename of original BL2 file to modify.
    """
    self._out.Info('Configuring BL2')
    bl2 = os.path.join(self._tools.outdir, 'updated-spl%s.bin' % name)
    data = self._tools.ReadFile(orig_bl2)
    self._tools.WriteFile(bl2, data)

    # Locate the parameter block
    data = self._tools.ReadFile(bl2)
    marker = struct.pack('<L', 0xdeadbeef)
    pos = data.rfind(marker)
    if not pos:
      raise CmdError("Could not find machine parameter block in '%s'" %
          orig_bl2)
    data = self._UpdateParameters(fdt, spl_load_size, data, pos)
    data = self._UpdateChecksum(data)
    self._tools.WriteFile(bl2, data)
    return bl2
