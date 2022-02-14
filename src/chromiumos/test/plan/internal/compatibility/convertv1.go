// Copyright 2022 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// Package compatibility provides functions for backwards compatiblity with
// test platform.
package compatibility

import (
	"fmt"

	"github.com/golang/glog"
	testpb "go.chromium.org/chromiumos/config/go/test/api"
	test_api_v1 "go.chromium.org/chromiumos/config/go/test/api/v1"
	"go.chromium.org/chromiumos/infra/proto/go/chromiumos"
	"go.chromium.org/chromiumos/infra/proto/go/testplans"
	bbpb "go.chromium.org/luci/buildbucket/proto"
	"go.chromium.org/luci/common/data/stringset"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/structpb"
	"google.golang.org/protobuf/types/known/wrapperspb"
)

// getAttrFromCriteria finds the DutCriterion with attribute id attr in
// criteria. If the DutCriterion is not found or has more than one value, an
// error is returned.
func getAttrFromCriteria(criteria []*testpb.DutCriterion, attr *testpb.DutAttribute) (string, error) {
	for _, criterion := range criteria {
		isAttr := false
		if criterion.GetAttributeId().GetValue() == attr.GetId().GetValue() {
			isAttr = true
		} else {
			for _, alias := range attr.GetAliases() {
				if criterion.GetAttributeId().GetValue() == alias {
					isAttr = true
					break
				}
			}
		}

		if isAttr {
			if len(criterion.GetValues()) != 1 {
				return "", fmt.Errorf("only DutCriterion with exactly one value supported, got %q", criterion)
			}

			return criterion.GetValues()[0], nil
		}
	}

	return "", fmt.Errorf("attribute %q not found in DutCriterion %q", attr.GetId().GetValue(), criteria)
}

// extractFromProtoStruct returns the path pointed to by fields. For example,
// for the struct `"a": {"b": 1}`, if fields is ["a", "b"], 1 is returned. The
// bool return value indicates if the path was found.
func extractFromProtoStruct(s *structpb.Struct, fields ...string) (*structpb.Value, bool) {
	var value *structpb.Value

	for i, field := range fields {
		var ok bool
		value, ok = s.Fields[field]
		if !ok {
			return nil, false
		}

		// All of the fields before the last one must be structs (otherwise
		// fields cannot form a valid path). Since the last field may not be a
		// struct, (and we don't need to use the struct if it is) break here and
		// return the value. Otherwise check that the value is a struct, and
		// set s to the new struct.
		if i == len(fields)-1 {
			break
		}

		s = value.GetStructValue()
		if s == nil {
			return nil, false
		}
	}

	return value, true
}

// extractStringFromProtoStruct invokes extractFromProtoStruct, but also checks
// that the value pointed to by fields is a non-empty string.
func extractStringFromProtoStruct(s *structpb.Struct, fields ...string) (string, bool) {
	v, ok := extractFromProtoStruct(s, fields...)
	if !ok {
		return "", false
	}

	if v.GetStringValue() == "" {
		return "", false
	}

	return v.GetStringValue(), true
}

// buildInfo describes properties parsed from a Buildbucket build.
type buildInfo struct {
	buildTarget string
	builderName string
	payload     *testplans.BuildPayload
}

// parseBuildProtos parses serialized Buildbucket Build protos and extracts
// properties into buildInfos.
func parseBuildProtos(buildbucketProtos []*testplans.ProtoBytes) ([]*buildInfo, error) {
	buildInfos := []*buildInfo{}

	// The presence of any one of these artifacts is enough to tell us that this
	// build should be considered for testing.
	testArtifacts := stringset.NewFromSlice(
		"AUTOTEST_FILES",
		"IMAGE_ZIP",
		"PINNED_GUEST_IMAGES",
		"TAST_FILES",
		"TEST_UPDATE_PAYLOAD",
	)

	for _, protoBytes := range buildbucketProtos {
		build := &bbpb.Build{}
		if err := proto.Unmarshal(protoBytes.SerializedProto, build); err != nil {
			return nil, err
		}

		pointless, ok := extractFromProtoStruct(build.GetOutput().GetProperties(), "pointless_build")
		if ok && pointless.GetBoolValue() {
			glog.Warningf("build %q is pointless, skipping", build.GetBuilder().GetBuilder())
			continue
		}

		buildTarget, ok := extractStringFromProtoStruct(
			build.GetInput().GetProperties(),
			"build_target", "name",
		)
		if !ok {
			glog.Warningf("build_target.name not found in input properties of build %q, skipping", build.GetBuilder().GetBuilder())
			continue
		}

		filesByArtifact, ok := extractFromProtoStruct(
			build.GetOutput().GetProperties(),
			"artifacts", "files_by_artifact",
		)
		if !ok {
			glog.Warningf("artifacts.files_by_artifact not found in output properties of build %q, skipping", build.GetBuilder().GetBuilder())
			continue
		}

		if filesByArtifact.GetStructValue() == nil {
			return nil, fmt.Errorf("artifacts.files_by_artifact must be a non-empty struct")
		}

		foundTestArtifact := false
		for field := range filesByArtifact.GetStructValue().GetFields() {
			if testArtifacts.Has(field) {
				foundTestArtifact = true
				break
			}
		}

		if !foundTestArtifact {
			glog.Warningf("no test artifacts found for build %q, skipping", build.GetBuilder().GetBuilder())
			continue
		}

		artifacts_gs_bucket, ok := extractStringFromProtoStruct(
			build.GetOutput().GetProperties(),
			"artifacts", "gs_bucket",
		)
		if !ok {
			return nil, fmt.Errorf("artifacts.gs_bucket not found for build %q", build.GetBuilder().GetBuilder())
		}

		artifacts_gs_path, ok := extractStringFromProtoStruct(
			build.GetOutput().GetProperties(),
			"artifacts", "gs_path",
		)
		if !ok {
			return nil, fmt.Errorf("artifacts.gs_path not found for build %q", build.GetBuilder().GetBuilder())
		}

		buildInfos = append(buildInfos, &buildInfo{
			buildTarget: buildTarget,
			builderName: build.GetBuilder().GetBuilder(),
			payload: &testplans.BuildPayload{
				ArtifactsGsBucket: artifacts_gs_bucket,
				ArtifactsGsPath:   artifacts_gs_path,
				FilesByArtifact:   filesByArtifact.GetStructValue(),
			},
		},
		)
	}

	return buildInfos, nil
}

type suiteInfo struct {
	program string
	pool    string
	suite   string
}

// extractSuiteInfos returns a map from program name to suiteInfos for the
// program. There is one suiteInfo per CoverageRule in hwTestPlans.
func extractSuiteInfos(
	hwTestPlans []*test_api_v1.HWTestPlan,
	dutAttributeList *testpb.DutAttributeList,
) (map[string][]*suiteInfo, error) {
	// Find the program and pool attributes in the DutAttributeList.
	var programAttr, poolAttr *testpb.DutAttribute
	for _, attr := range dutAttributeList.GetDutAttributes() {
		if attr.Id.Value == "attr-program" {
			programAttr = attr
		} else if attr.Id.Value == "swarming-pool" {
			poolAttr = attr
		}
	}

	if programAttr == nil {
		return nil, fmt.Errorf("\"attr-program\" not found in DutAttributeList")
	}

	if poolAttr == nil {
		return nil, fmt.Errorf("\"swarming-pool\" not found in DutAttributeList")
	}

	programToSuiteInfos := map[string][]*suiteInfo{}

	for _, hwTestPlan := range hwTestPlans {
		for _, rule := range hwTestPlan.GetCoverageRules() {
			if len(rule.GetDutTargets()) != 1 {
				return nil, fmt.Errorf("expected exactly one DutTarget in CoverageRule, got %q", rule)
			}

			dutTarget := rule.GetDutTargets()[0]

			program, err := getAttrFromCriteria(dutTarget.GetCriteria(), programAttr)
			if err != nil {
				return nil, err
			}

			if _, ok := programToSuiteInfos[program]; !ok {
				programToSuiteInfos[program] = []*suiteInfo{}
			}

			pool, err := getAttrFromCriteria(dutTarget.GetCriteria(), poolAttr)
			if err != nil {
				return nil, err
			}

			if len(dutTarget.GetCriteria()) != 2 {
				return nil, fmt.Errorf(
					"expected DutTarget to use exactly criteria %q and %q, got %q",
					programAttr.GetId().GetValue(), poolAttr.GetId().GetValue(), dutTarget,
				)
			}

			for _, suite := range rule.GetTestSuites() {
				testCaseIds := suite.GetTestCaseIds()
				if testCaseIds == nil {
					return nil, fmt.Errorf("Only TestCaseIds supported in TestSuites, got %q", suite)
				}

				for _, id := range testCaseIds.GetTestCaseIds() {
					programToSuiteInfos[program] = append(
						programToSuiteInfos[program],
						&suiteInfo{
							program: program,
							pool:    pool,
							suite:   id.Value,
						})
				}
			}
		}
	}

	return programToSuiteInfos, nil
}

// ToCTP1 converts a HWTestPlan to a GenerateTestPlansResponse, which can be
// used with CTP1.
//
// HWTestPlan protos target CTP2, this method is meant to provide backwards
// compatibility with CTP1. Because CTP1 does not support rules-based testing,
// there are some limitations to the HWTestPlans that can be converted:
// - Both the "attr-program" and "swarming-pool" DutAttributes must be used in
//   each DutTarget, and only these DutAttributes are allowed, i.e. each
//   DutTarget must use exactly these attributes.
// - Only one value per DutCriterion is allowed, e.g. a rule that specifies a
// 	 test should run on either "programA" or "programB" is not allowed.
// - Only TestCaseIds are supported (no tag-based testing).
//
// generateTestPlanReq is needed to provide Build protos for the builds being
// tested. dutAttributeList must contain the "attr-program" and "swarming-pool"
// DutAttributes.
func ToCTP1(
	hwTestPlans []*test_api_v1.HWTestPlan,
	generateTestPlanReq *testplans.GenerateTestPlanRequest,
	dutAttributeList *testpb.DutAttributeList,
) (*testplans.GenerateTestPlanResponse, error) {
	buildInfos, err := parseBuildProtos(generateTestPlanReq.GetBuildbucketProtos())
	if err != nil {
		return nil, err
	}

	programToSuiteInfos, err := extractSuiteInfos(hwTestPlans, dutAttributeList)
	if err != nil {
		return nil, err
	}

	var hwTestUnits []*testplans.HwTestUnit

	// Join the buildInfos and suiteInfos on the suite's program name and
	// build's build target. Each build maps to one HwTestUnit, each suite maps
	// to one HwTestCfg_HwTest.
	for _, buildInfo := range buildInfos {
		suiteInfos, ok := programToSuiteInfos[buildInfo.buildTarget]
		if !ok {
			glog.Warningf("no suites found for build %q, skipping tests", buildInfo.buildTarget)
			continue
		}

		var hwTests []*testplans.HwTestCfg_HwTest
		for _, suiteInfo := range suiteInfos {
			hwTests = append(hwTests, &testplans.HwTestCfg_HwTest{
				Suite:       suiteInfo.suite,
				SkylabBoard: suiteInfo.program,
				Pool:        suiteInfo.pool,
				Common: &testplans.TestSuiteCommon{
					DisplayName: fmt.Sprintf("%s.%s", suiteInfo.program, suiteInfo.suite),
					// TODO(b/218319842): Set critical value based on v2 test disablement config.
					Critical: &wrapperspb.BoolValue{
						Value: true,
					},
				},
			})
		}

		hwTestUnit := &testplans.HwTestUnit{
			Common: &testplans.TestUnitCommon{
				BuildTarget: &chromiumos.BuildTarget{
					Name: buildInfo.buildTarget,
				},
				BuilderName:  buildInfo.builderName,
				BuildPayload: buildInfo.payload,
			},
			HwTestCfg: &testplans.HwTestCfg{
				HwTest: hwTests,
			},
		}
		hwTestUnits = append(hwTestUnits, hwTestUnit)
	}

	return &testplans.GenerateTestPlanResponse{
		HwTestUnits: hwTestUnits,
	}, nil
}
