// Copyright 2021 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package testplan_test

import (
	"testing"

	configpb "go.chromium.org/chromiumos/config/go/api"
	"go.chromium.org/chromiumos/config/go/api/software"
	buildpb "go.chromium.org/chromiumos/config/go/build/api"
	"go.chromium.org/chromiumos/config/go/payload"
	testpb "go.chromium.org/chromiumos/config/go/test/api"

	testplan "chromiumos/test/plan/internal"
)

// buildMetadata is a convenience to reduce boilerplate when creating
// SystemImage_BuildMetadata in test cases.
func buildMetadata(overlay, kernelVersion, chipsetOverlay, arcVersion string) *buildpb.SystemImage_BuildMetadata {
	return &buildpb.SystemImage_BuildMetadata{
		BuildTarget: &buildpb.SystemImage_BuildTarget{
			PortageBuildTarget: &buildpb.Portage_BuildTarget{
				OverlayName: overlay,
			},
		},
		PackageSummary: &buildpb.SystemImage_BuildMetadata_PackageSummary{
			Kernel: &buildpb.SystemImage_BuildMetadata_Kernel{
				Version: kernelVersion,
			},
			Chipset: &buildpb.SystemImage_BuildMetadata_Chipset{
				Overlay: chipsetOverlay,
			},
			Arc: &buildpb.SystemImage_BuildMetadata_Arc{
				Version: arcVersion,
			},
		},
	}
}

// flatConfig is a convenience to reduce boilerplate when creating FlatConfig
// in test cases.
func flatConfig(program, design, designConfig string, firmwareROVersion *buildpb.Version) *payload.FlatConfig {
	return &payload.FlatConfig{
		Program:        &configpb.Program{Id: &configpb.ProgramId{Value: program}},
		HwDesign:       &configpb.Design{Id: &configpb.DesignId{Value: design}},
		HwDesignConfig: &configpb.Design_Config{Id: &configpb.DesignConfigId{Value: designConfig}},
		SwConfig: &software.SoftwareConfig{
			Firmware: &buildpb.FirmwareConfig{
				MainRoPayload: &buildpb.FirmwarePayload{
					Version: firmwareROVersion,
				},
			},
		},
	}
}

var buildMetadataList = &buildpb.SystemImage_BuildMetadataList{
	Values: []*buildpb.SystemImage_BuildMetadata{
		buildMetadata("project1", "4.14", "chipsetA", "P"),
		buildMetadata("project2", "4.14", "chipsetB", "R"),
		buildMetadata("project3", "5.4", "chipsetA", ""),
	},
}

var dutAttributeList = &testpb.DutAttributeList{
	DutAttributes: []*testpb.DutAttribute{
		{
			Id: &testpb.DutAttribute_Id{Value: "fingerprint_location"},
			DataSource: &testpb.DutAttribute_FlatConfigSource_{
				FlatConfigSource: &testpb.DutAttribute_FlatConfigSource{
					Fields: []*testpb.DutAttribute_FieldSpec{
						{
							Path: "design_list.configs.hardware_features.fingerprint.location",
						},
					},
				},
			},
		},
		{
			Id: &testpb.DutAttribute_Id{Value: "system_build_target"},
			DataSource: &testpb.DutAttribute_FlatConfigSource_{
				FlatConfigSource: &testpb.DutAttribute_FlatConfigSource{
					Fields: []*testpb.DutAttribute_FieldSpec{
						{
							Path: "software_configs.system_build_target.portage_build_target.overlay_name",
						},
					},
				},
			},
		},
	},
}

var flatConfigList = &payload.FlatConfigList{
	Values: []*payload.FlatConfig{
		flatConfig("ProgA", "Design1", "Config1", &buildpb.Version{Major: 123, Minor: 4, Patch: 5}),
		flatConfig("ProgA", "Design1", "Config2", &buildpb.Version{Major: 123, Minor: 4, Patch: 5}),
		flatConfig("ProgA", "Design2", "Config1", &buildpb.Version{Major: 123, Minor: 0, Patch: 0}),
		flatConfig("ProgB", "Design20", "Config1", &buildpb.Version{Major: 123, Minor: 4, Patch: 0}),
	},
}

func TestGenerateErrors(t *testing.T) {
	tests := []struct {
		name              string
		planFilenames     []string
		buildMetadataList *buildpb.SystemImage_BuildMetadataList
		dutAttributeList  *testpb.DutAttributeList
		flatConfigList    *payload.FlatConfigList
	}{
		{
			name:              "empty planFilenames",
			planFilenames:     []string{},
			buildMetadataList: buildMetadataList,
			dutAttributeList:  dutAttributeList,
			flatConfigList:    flatConfigList,
		},
		{
			name:              "nil buildMetadataList",
			planFilenames:     []string{"plan1.star"},
			buildMetadataList: nil,
			dutAttributeList:  dutAttributeList,
			flatConfigList:    flatConfigList,
		},
		{
			name:              "nil dutAttributeList",
			planFilenames:     []string{"plan1.star"},
			buildMetadataList: buildMetadataList,
			dutAttributeList:  nil,
			flatConfigList:    flatConfigList,
		},
		{
			name:              "nil FlatConfigList",
			planFilenames:     []string{"plan1.star"},
			buildMetadataList: buildMetadataList,
			dutAttributeList:  dutAttributeList,
			flatConfigList:    nil,
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if _, err := testplan.Generate(
				test.planFilenames, test.buildMetadataList, test.dutAttributeList, flatConfigList,
			); err == nil {
				t.Error("Expected error from Generate")
			}
		})
	}
}
