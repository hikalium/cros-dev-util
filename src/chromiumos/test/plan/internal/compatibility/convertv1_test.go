// Copyright 2022 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
package compatibility_test

import (
	"math/rand"
	"strings"
	"testing"

	"chromiumos/test/plan/internal/compatibility"

	"github.com/golang/protobuf/proto"
	"github.com/google/go-cmp/cmp"
	testpb "go.chromium.org/chromiumos/config/go/test/api"
	test_api_v1 "go.chromium.org/chromiumos/config/go/test/api/v1"
	"go.chromium.org/chromiumos/infra/proto/go/chromiumos"
	"go.chromium.org/chromiumos/infra/proto/go/testplans"
	bbpb "go.chromium.org/luci/buildbucket/proto"
	"google.golang.org/protobuf/testing/protocmp"
	"google.golang.org/protobuf/types/known/structpb"
	"google.golang.org/protobuf/types/known/wrapperspb"
)

// newStruct is a convenience method to build a structpb.Struct from a map of
// string -> interface. For example:
//
// newStruct(t, map[string]interface{}{
// "a": 1, "b": []interface{}{"c", "d"}
// })
//
// Any errors will be passed to t.Fatal. See structpb.NewValue for more info
// on how Go interfaces are converted to structpb.Struct.
func newStruct(t *testing.T, fields map[string]interface{}) *structpb.Struct {
	s := &structpb.Struct{Fields: map[string]*structpb.Value{}}

	for key, val := range fields {
		valPb, err := structpb.NewValue(val)
		if err != nil {
			t.Fatal(err)
		}

		s.Fields[key] = valPb
	}

	return s
}

var hwTestPlans = []*test_api_v1.HWTestPlan{
	{
		CoverageRules: []*testpb.CoverageRule{
			{
				TestSuites: []*testpb.TestSuite{
					{
						Spec: &testpb.TestSuite_TestCaseIds{
							TestCaseIds: &testpb.TestCaseIdList{
								TestCaseIds: []*testpb.TestCase_Id{
									{
										Value: "suite1",
									},
									{
										Value: "suite2",
									},
									// Add a suite twice, it should be de-duped.
									{
										Value: "suite1",
									},
								},
							},
						},
					},
				},
				DutTargets: []*testpb.DutTarget{
					{
						Criteria: []*testpb.DutCriterion{
							{
								AttributeId: &testpb.DutAttribute_Id{
									Value: "attr-program",
								},
								// "boardA" will be chosen, since it is critical and has the lowest priority.
								Values: []string{"boardC", "boardA", "boardB", "non-critical-board"},
							},
							{
								AttributeId: &testpb.DutAttribute_Id{
									Value: "swarming-pool",
								},
								Values: []string{"DUT_POOL_QUOTA"},
							},
						},
					},
				},
			},
			{
				TestSuites: []*testpb.TestSuite{
					{

						Spec: &testpb.TestSuite_TestCaseIds{
							TestCaseIds: &testpb.TestCaseIdList{
								TestCaseIds: []*testpb.TestCase_Id{
									{
										Value: "suite3",
									},
								},
							},
						},
					},
				},
				DutTargets: []*testpb.DutTarget{
					{
						Criteria: []*testpb.DutCriterion{
							{
								AttributeId: &testpb.DutAttribute_Id{
									Value: "attr-program",
								},
								Values: []string{"boardA"},
							},
							{
								AttributeId: &testpb.DutAttribute_Id{
									Value: "attr-model",
								},
								Values: []string{"model1"},
							},
							{
								AttributeId: &testpb.DutAttribute_Id{
									Value: "swarming-pool",
								},
								Values: []string{"DUT_POOL_QUOTA"},
							},
						},
					},
				},
			},
		},
	},
}

var vmTestPlans = []*test_api_v1.VMTestPlan{
	{
		CoverageRules: []*testpb.CoverageRule{
			{
				Name: "vmrule",
				TestSuites: []*testpb.TestSuite{
					{
						Name: "tast_vm_suite1",
						Spec: &testpb.TestSuite_TestCaseTagCriteria_{
							TestCaseTagCriteria: &testpb.TestSuite_TestCaseTagCriteria{
								Tags:        []string{"\"group:mainline\"", "\"dep:depA\""},
								TagExcludes: []string{"informational"},
							},
						},
					},
					{
						Name: "tast_gce_suite2",
						Spec: &testpb.TestSuite_TestCaseTagCriteria_{
							TestCaseTagCriteria: &testpb.TestSuite_TestCaseTagCriteria{
								Tags: []string{"\"group:mainline\"", "informational"},
							},
						},
					},
					// Add suites twice, they should be de-duped.
					{
						Name: "tast_vm_suite1",
						Spec: &testpb.TestSuite_TestCaseTagCriteria_{
							TestCaseTagCriteria: &testpb.TestSuite_TestCaseTagCriteria{
								Tags:        []string{"\"group:mainline\"", "\"dep:depA\""},
								TagExcludes: []string{"informational"},
							},
						},
					},
					{
						Name: "tast_gce_suite2",
						Spec: &testpb.TestSuite_TestCaseTagCriteria_{
							TestCaseTagCriteria: &testpb.TestSuite_TestCaseTagCriteria{
								Tags: []string{"\"group:mainline\"", "informational"},
							},
						},
					},
				},
				DutTargets: []*testpb.DutTarget{
					{
						Criteria: []*testpb.DutCriterion{
							{
								AttributeId: &testpb.DutAttribute_Id{
									Value: "attr-program",
								},
								Values: []string{"vmboardA", "vmboardB"},
							},
							{
								AttributeId: &testpb.DutAttribute_Id{
									Value: "swarming-pool",
								},
								Values: []string{"VM_POOL"},
							},
						},
					},
				},
			},
		},
	},
}

func serializeOrFatal(t *testing.T, m proto.Message) *testplans.ProtoBytes {
	b, err := proto.Marshal(m)
	if err != nil {
		t.Fatal(err)
	}

	return &testplans.ProtoBytes{SerializedProto: b}
}

func getSerializedBuilds(t *testing.T) []*testplans.ProtoBytes {
	build1 := &bbpb.Build{
		Builder: &bbpb.BuilderID{
			Builder: "cq-builderA",
		},
		Input: &bbpb.Build_Input{
			Properties: newStruct(t, map[string]interface{}{
				"build_target": map[string]interface{}{
					"name": "boardA",
				},
			}),
		},
		Output: &bbpb.Build_Output{
			Properties: newStruct(t, map[string]interface{}{
				"artifacts": map[string]interface{}{
					"gs_bucket": "testgsbucket",
					"gs_path":   "testgspathA",
					"files_by_artifact": map[string]interface{}{
						"AUTOTEST_FILES": []interface{}{"file1", "file2"},
					},
				},
			}),
		},
		Critical: bbpb.Trinary_YES,
	}

	build2 := &bbpb.Build{
		Builder: &bbpb.BuilderID{
			Builder: "cq-builderB",
		},
		Input: &bbpb.Build_Input{
			Properties: newStruct(t, map[string]interface{}{
				"build_target": map[string]interface{}{
					"name": "boardB",
				},
			}),
		},
		Output: &bbpb.Build_Output{
			Properties: newStruct(t, map[string]interface{}{
				"artifacts": map[string]interface{}{
					"gs_bucket": "testgsbucket",
					"gs_path":   "testgspathB",
					"files_by_artifact": map[string]interface{}{
						"testartifact": []interface{}{"file1", "file2"},
					},
				},
			}),
		},
		Critical: bbpb.Trinary_YES,
	}

	build3 := &bbpb.Build{
		Builder: &bbpb.BuilderID{
			Builder: "cq-builderC",
		},
		Input: &bbpb.Build_Input{
			Properties: newStruct(t, map[string]interface{}{
				"build_target": map[string]interface{}{
					"name": "boardC",
				},
			}),
		},
		Output: &bbpb.Build_Output{
			Properties: newStruct(t, map[string]interface{}{
				"artifacts": map[string]interface{}{
					"gs_bucket": "testgsbucket",
					"gs_path":   "testgspathC",
					"files_by_artifact": map[string]interface{}{
						"AUTOTEST_FILES": []interface{}{"file1", "file2"},
					},
				},
			}),
		},
	}

	build4 := &bbpb.Build{
		Builder: &bbpb.BuilderID{
			Builder: "non-critical-builder",
		},
		Input: &bbpb.Build_Input{
			Properties: newStruct(t, map[string]interface{}{
				"build_target": map[string]interface{}{
					"name": "non-critical-board",
				},
			}),
		},
		Output: &bbpb.Build_Output{
			Properties: newStruct(t, map[string]interface{}{
				"artifacts": map[string]interface{}{
					"gs_bucket": "testgsbucket",
					"gs_path":   "testgspath",
					"files_by_artifact": map[string]interface{}{
						"AUTOTEST_FILES": []interface{}{"file1", "file2"},
					},
				},
			}),
		},
		Critical: bbpb.Trinary_NO,
	}

	build5 := &bbpb.Build{
		Builder: &bbpb.BuilderID{
			Builder: "pointless-build",
		},
		Output: &bbpb.Build_Output{
			Properties: newStruct(t, map[string]interface{}{
				"pointless_build": true,
			}),
		},
	}

	build6 := &bbpb.Build{
		Builder: &bbpb.BuilderID{
			Builder: "no-build-target-build",
		},
		Input: &bbpb.Build_Input{
			Properties: newStruct(t, map[string]interface{}{
				"other_input_prop": 12,
			}),
		},
		Output: &bbpb.Build_Output{
			Properties: newStruct(t, map[string]interface{}{
				"artifacts": map[string]interface{}{
					"gs_bucket": "testgsbucket",
					"gs_path":   "testgspathB",
					"files_by_artifact": map[string]interface{}{
						"testartifact": []interface{}{"file1", "file2"},
					},
				},
			}),
		},
	}

	vmBuild := &bbpb.Build{
		Builder: &bbpb.BuilderID{
			Builder: "cq-vmBuilderA",
		},
		Input: &bbpb.Build_Input{
			Properties: newStruct(t, map[string]interface{}{
				"build_target": map[string]interface{}{
					"name": "vmboardA",
				},
			}),
		},
		Output: &bbpb.Build_Output{
			Properties: newStruct(t, map[string]interface{}{
				"artifacts": map[string]interface{}{
					"gs_bucket": "testgsbucket",
					"gs_path":   "testgspathA",
					"files_by_artifact": map[string]interface{}{
						"AUTOTEST_FILES": []interface{}{"file1", "file2"},
					},
				},
			}),
		},
		Critical: bbpb.Trinary_YES,
	}

	return []*testplans.ProtoBytes{
		serializeOrFatal(t, build1),
		serializeOrFatal(t, build2),
		serializeOrFatal(t, build3),
		serializeOrFatal(t, build4),
		serializeOrFatal(t, build5),
		serializeOrFatal(t, build6),
		serializeOrFatal(t, vmBuild),
	}
}

var dutAttributeList = &testpb.DutAttributeList{
	DutAttributes: []*testpb.DutAttribute{
		{
			Id: &testpb.DutAttribute_Id{
				Value: "attr-program",
			},
			Aliases: []string{"attr-board"},
		},
		{
			Id: &testpb.DutAttribute_Id{
				Value: "attr-design",
			},
			Aliases: []string{"attr-model"},
		},
		{
			Id: &testpb.DutAttribute_Id{
				Value: "swarming-pool",
			},
		},
	},
}

var boardPriorityList = &testplans.BoardPriorityList{
	BoardPriorities: []*testplans.BoardPriority{
		{
			SkylabBoard: "boardA", Priority: -100,
		},
		{
			SkylabBoard: "boardB", Priority: 100,
		},
	},
}

func TestToCTP1(t *testing.T) {
	req := &testplans.GenerateTestPlanRequest{
		BuildbucketProtos: getSerializedBuilds(t),
	}

	resp, err := compatibility.ToCTP1(
		rand.New(rand.NewSource(7)),
		hwTestPlans, vmTestPlans, req, dutAttributeList, boardPriorityList,
	)
	if err != nil {
		t.Fatal(err)
	}

	expectedResp := &testplans.GenerateTestPlanResponse{
		HwTestUnits: []*testplans.HwTestUnit{
			{
				Common: &testplans.TestUnitCommon{
					BuildTarget: &chromiumos.BuildTarget{
						Name: "boardA",
					},
					BuilderName: "cq-builderA",
					BuildPayload: &testplans.BuildPayload{
						ArtifactsGsBucket: "testgsbucket",
						ArtifactsGsPath:   "testgspathA",
						FilesByArtifact: newStruct(t, map[string]interface{}{
							"AUTOTEST_FILES": []interface{}{"file1", "file2"},
						}),
					},
				},
				HwTestCfg: &testplans.HwTestCfg{
					HwTest: []*testplans.HwTestCfg_HwTest{
						{
							Common: &testplans.TestSuiteCommon{
								DisplayName: "hw.boardA.model1.suite3",
								Critical:    wrapperspb.Bool(true),
							},
							Suite:       "suite3",
							SkylabBoard: "boardA",
							SkylabModel: "model1",
							Pool:        "DUT_POOL_QUOTA",
						},
						{
							Common: &testplans.TestSuiteCommon{
								DisplayName: "hw.boardA.suite1",
								Critical:    wrapperspb.Bool(true),
							},
							Suite:       "suite1",
							SkylabBoard: "boardA",
							Pool:        "DUT_POOL_QUOTA",
						},
						{
							Common: &testplans.TestSuiteCommon{
								DisplayName: "hw.boardA.suite2",
								Critical:    wrapperspb.Bool(true),
							},
							Suite:       "suite2",
							SkylabBoard: "boardA",
							Pool:        "DUT_POOL_QUOTA",
						},
					},
				},
			},
		},
		DirectTastVmTestUnits: []*testplans.TastVmTestUnit{
			{
				Common: &testplans.TestUnitCommon{
					BuildTarget: &chromiumos.BuildTarget{
						Name: "vmboardA",
					},
					BuilderName: "cq-vmBuilderA",
					BuildPayload: &testplans.BuildPayload{
						ArtifactsGsBucket: "testgsbucket",
						ArtifactsGsPath:   "testgspathA",
						FilesByArtifact: newStruct(t, map[string]interface{}{
							"AUTOTEST_FILES": []interface{}{"file1", "file2"},
						}),
					},
				},
				TastVmTestCfg: &testplans.TastVmTestCfg{
					TastVmTest: []*testplans.TastVmTestCfg_TastVmTest{
						{
							SuiteName: "tast_vm_suite1",
							TastTestExpr: []*testplans.TastVmTestCfg_TastTestExpr{
								{
									TestExpr: "\"group:mainline\" && \"dep:depA\" && !informational",
								},
							},
							Common: &testplans.TestSuiteCommon{DisplayName: "vm.vmboardA.tast_vm_suite1", Critical: wrapperspb.Bool(true)},
						},
					},
				},
			},
		},
		TastGceTestUnits: []*testplans.TastGceTestUnit{
			{
				Common: &testplans.TestUnitCommon{
					BuildTarget: &chromiumos.BuildTarget{
						Name: "vmboardA",
					},
					BuilderName: "cq-vmBuilderA",
					BuildPayload: &testplans.BuildPayload{
						ArtifactsGsBucket: "testgsbucket",
						ArtifactsGsPath:   "testgspathA",
						FilesByArtifact: newStruct(t, map[string]interface{}{
							"AUTOTEST_FILES": []interface{}{"file1", "file2"},
						}),
					},
				},
				TastGceTestCfg: &testplans.TastGceTestCfg{
					TastGceTest: []*testplans.TastGceTestCfg_TastGceTest{
						{
							SuiteName: "tast_gce_suite2",
							GceMetadata: &testplans.TastGceTestCfg_TastGceTest_GceMetadata{
								Project:     "chromeos-gce-tests",
								Zone:        "us-central1-a",
								MachineType: "n2-standard-8",
								Network:     "chromeos-gce-tests",
								Subnet:      "us-central1",
							},
							TastTestExpr: []*testplans.TastGceTestCfg_TastTestExpr{
								{
									TestExpr: "\"group:mainline\" && informational",
								},
							},
							Common: &testplans.TestSuiteCommon{
								DisplayName: "gce.vmboardA.tast_gce_suite2",
								Critical:    wrapperspb.Bool(true),
							},
						},
					},
				},
			},
		},
	}
	if diff := cmp.Diff(expectedResp, resp, protocmp.Transform()); diff != "" {
		t.Errorf("ToCTP1Response returned unexpected diff (-want +got):\n%s", diff)
	}
}

func TestToCTP1Errors(t *testing.T) {
	testCases := []struct {
		name             string
		hwTestPlans      []*test_api_v1.HWTestPlan
		vmTestPlans      []*test_api_v1.VMTestPlan
		dutAttributeList *testpb.DutAttributeList
		err              string
	}{
		{
			name:        "missing program DUT attribute",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"DUT_POOL_QUOTA"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "attribute \"attr-program\" not found in DutCriterion",
		},
		{
			name:        "missing pool DUT attribute",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "attribute \"swarming-pool\" not found in DutCriterion",
		},
		{

			name:        "missing pool DUT attribute",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
		},
		{
			name:        "criteria with no values",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "only DutCriterion with at least one value supported",
		},
		{
			name:        "invalid DUT attribute",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"DUT_POOL_QUOTA"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-design",
											},
											Values: []string{"model1"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "fp",
											},
											Values: []string{"fp1"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "expected DutTarget to use criteria \"attr-program\" and \"swarming-pool\", and optionally \"attr-design\"",
		},
		{
			name:        "multiple pool values",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"testpoolA", "testpoolB"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"boardA", "boardB"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "only DutCriteria with exactly one \"pool\" argument are supported",
		},
		{

			name:        "multiple design values",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"testpoolA"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"boardA"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-design",
											},
											Values: []string{"model1", "model2"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "only DutCriteria with exactly one \"attr-design\" argument are supported",
		},
		{
			name:        "test tags used",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"DUT_POOL_QUOTA"},
										},
									},
								},
							},
							TestSuites: []*testpb.TestSuite{
								{
									Spec: &testpb.TestSuite_TestCaseTagCriteria_{
										TestCaseTagCriteria: &testpb.TestSuite_TestCaseTagCriteria{
											Tags: []string{"kernel"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "TestCaseTagCriteria are only valid for VM tests",
		},
		{
			name:        "multiple DUT targets",
			vmTestPlans: vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA"},
										},
									},
								},
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programB"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "expected exactly one DutTarget in CoverageRule",
		},
		{
			name: "invalid DutAttributeList",
			dutAttributeList: &testpb.DutAttributeList{
				DutAttributes: []*testpb.DutAttribute{
					{
						Id: &testpb.DutAttribute_Id{
							Value: "otherdutattr",
						},
					},
				},
			},
			err: "\"attr-program\" not found in DutAttributeList",
		},
		{
			name:             "multiple programs with design",
			dutAttributeList: dutAttributeList,
			vmTestPlans:      vmTestPlans,
			hwTestPlans: []*test_api_v1.HWTestPlan{
				{
					Id: &test_api_v1.HWTestPlan_TestPlanId{
						Value: "testplan1",
					},
					CoverageRules: []*testpb.CoverageRule{
						{
							Name: "invalidrule",
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA", "programB"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"DUT_POOL_QUOTA"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-design",
											},
											Values: []string{"model1"},
										},
									},
								},
							},
						},
					},
				},
			},
			err: "if \"attr-design\" is specified, multiple \"attr-programs\" cannot be used",
		},
		{
			name:        "invalid VM test name",
			hwTestPlans: hwTestPlans,
			vmTestPlans: []*test_api_v1.VMTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							TestSuites: []*testpb.TestSuite{
								{
									Name: "vmsuite1",
									Spec: &testpb.TestSuite_TestCaseTagCriteria_{
										TestCaseTagCriteria: &testpb.TestSuite_TestCaseTagCriteria{
											Tags: []string{"tagA"},
										},
									},
								},
							},
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA", "programB"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"DUT_POOL_QUOTA"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "VM suite names must start with either \"tast_vm\" or \"tast_gce\" in CTP1 compatibility mode",
		},
		{

			name:        "VM test with id list",
			hwTestPlans: hwTestPlans,
			vmTestPlans: []*test_api_v1.VMTestPlan{
				{
					CoverageRules: []*testpb.CoverageRule{
						{
							TestSuites: []*testpb.TestSuite{
								{
									Name: "tast_vm_suite1",
									Spec: &testpb.TestSuite_TestCaseIds{
										TestCaseIds: &testpb.TestCaseIdList{
											TestCaseIds: []*testpb.TestCase_Id{
												{
													Value: "testcaseA",
												},
											},
										},
									},
								},
							},
							DutTargets: []*testpb.DutTarget{
								{
									Criteria: []*testpb.DutCriterion{
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "attr-program",
											},
											Values: []string{"programA", "programB"},
										},
										{
											AttributeId: &testpb.DutAttribute_Id{
												Value: "swarming-pool",
											},
											Values: []string{"DUT_POOL_QUOTA"},
										},
									},
								},
							},
						},
					},
				},
			},
			dutAttributeList: dutAttributeList,
			err:              "TestCaseIdLists are only valid for HW tests",
		},
	}

	req := &testplans.GenerateTestPlanRequest{
		BuildbucketProtos: getSerializedBuilds(t),
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			_, err := compatibility.ToCTP1(
				rand.New(rand.NewSource(7)),
				tc.hwTestPlans, tc.vmTestPlans, req, tc.dutAttributeList, boardPriorityList,
			)
			if err == nil {
				t.Error("Expected error from ToCTP1")
			}

			if !strings.Contains(err.Error(), tc.err) {
				t.Errorf("Expected error to contain %q, got %q", tc.err, err.Error())
			}
		})
	}
}
