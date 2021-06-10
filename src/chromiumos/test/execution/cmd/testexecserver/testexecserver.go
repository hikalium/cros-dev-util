// Copyright 2021 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Package main implements the executionservice server
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/golang/protobuf/jsonpb"
	"go.chromium.org/chromiumos/config/go/test/api"

	"chromiumos/test/execution/cmd/testexecserver/internal/driver"
)

// runTests runs the requested tests.
func runTests(ctx context.Context, logger *log.Logger, testType string, req *api.RunTestsRequest) (*api.RunTestsResponse, error) {
	var testDriver driver.Driver
	if testType == "tast" {
		testDriver = driver.NewTastDriver(logger)
	}
	var tests []string
	for _, suite := range req.TestSuites {
		for _, tc := range suite.TestCaseIds.TestCaseIds {
			tests = append(tests, tc.Value)
		}
		// TO-DO Support Tags
	}

	if testDriver != nil {
		return testDriver.RunTests(ctx, "", req.Dut.PrimaryHost, tests)
	}
	return nil, fmt.Errorf("unknown test driver: %v", testType)
}

// readInput reads an execution_service json file and returns a pointer to RunTestsRequest.
func readInput(fileName string) (*api.RunTestsRequest, error) {
	f, err := os.Open(fileName)
	if err != nil {
		return nil, fmt.Errorf("fail to read file %v: %v", fileName, err)
	}
	req := api.RunTestsRequest{}
	if err := jsonpb.Unmarshal(f, &req); err != nil {
		return nil, fmt.Errorf("fail to unmarshal file %v: %v", fileName, err)
	}
	return &req, nil
}

// writeOutput writes a RunTestsResponse json.
func writeOutput(output string, resp *api.RunTestsResponse) error {
	f, err := os.Create(output)
	if err != nil {
		return fmt.Errorf("fail to create file %v: %v", output, err)
	}
	m := jsonpb.Marshaler{}
	if err := m.Marshal(f, resp); err != nil {
		return fmt.Errorf("failed to marshall response to file %v: %v", output, err)
	}
	return nil
}