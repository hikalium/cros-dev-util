// Copyright 2021 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Code generated by MockGen. DO NOT EDIT.
// Source: test/provision/cmd/provisionserver/bootstrap/services/serviceadapterinterface.go

// Package mock_services is a generated GoMock package.
package mock_services

import (
	context "context"
	reflect "reflect"

	gomock "github.com/golang/mock/gomock"
)

// MockServiceAdapterInterface is a mock of ServiceAdapterInterface interface.
type MockServiceAdapterInterface struct {
	ctrl     *gomock.Controller
	recorder *MockServiceAdapterInterfaceMockRecorder
}

// MockServiceAdapterInterfaceMockRecorder is the mock recorder for MockServiceAdapterInterface.
type MockServiceAdapterInterfaceMockRecorder struct {
	mock *MockServiceAdapterInterface
}

// NewMockServiceAdapterInterface creates a new mock instance.
func NewMockServiceAdapterInterface(ctrl *gomock.Controller) *MockServiceAdapterInterface {
	mock := &MockServiceAdapterInterface{ctrl: ctrl}
	mock.recorder = &MockServiceAdapterInterfaceMockRecorder{mock}
	return mock
}

// EXPECT returns an object that allows the caller to indicate expected use.
func (m *MockServiceAdapterInterface) EXPECT() *MockServiceAdapterInterfaceMockRecorder {
	return m.recorder
}

// CopyData mocks base method.
func (m *MockServiceAdapterInterface) CopyData(ctx context.Context, sourceUrl, destPath string) error {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "CopyData", ctx, sourceUrl, destPath)
	ret0, _ := ret[0].(error)
	return ret0
}

// CopyData indicates an expected call of CopyData.
func (mr *MockServiceAdapterInterfaceMockRecorder) CopyData(ctx, sourceUrl, destPath interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "CopyData", reflect.TypeOf((*MockServiceAdapterInterface)(nil).CopyData), ctx, sourceUrl, destPath)
}

// CreateDirectories mocks base method.
func (m *MockServiceAdapterInterface) CreateDirectories(ctx context.Context, dirs []string) error {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "CreateDirectories", ctx, dirs)
	ret0, _ := ret[0].(error)
	return ret0
}

// CreateDirectories indicates an expected call of CreateDirectories.
func (mr *MockServiceAdapterInterfaceMockRecorder) CreateDirectories(ctx, dirs interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "CreateDirectories", reflect.TypeOf((*MockServiceAdapterInterface)(nil).CreateDirectories), ctx, dirs)
}

// DeleteDirectory mocks base method.
func (m *MockServiceAdapterInterface) DeleteDirectory(ctx context.Context, dir string) error {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "DeleteDirectory", ctx, dir)
	ret0, _ := ret[0].(error)
	return ret0
}

// DeleteDirectory indicates an expected call of DeleteDirectory.
func (mr *MockServiceAdapterInterfaceMockRecorder) DeleteDirectory(ctx, dir interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "DeleteDirectory", reflect.TypeOf((*MockServiceAdapterInterface)(nil).DeleteDirectory), ctx, dir)
}

// PathExists mocks base method.
func (m *MockServiceAdapterInterface) PathExists(ctx context.Context, path string) (bool, error) {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "PathExists", ctx, path)
	ret0, _ := ret[0].(bool)
	ret1, _ := ret[1].(error)
	return ret0, ret1
}

// PathExists indicates an expected call of PathExists.
func (mr *MockServiceAdapterInterfaceMockRecorder) PathExists(ctx, path interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "PathExists", reflect.TypeOf((*MockServiceAdapterInterface)(nil).PathExists), ctx, path)
}

// PipeData mocks base method.
func (m *MockServiceAdapterInterface) PipeData(ctx context.Context, sourceUrl, pipeCommand string) error {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "PipeData", ctx, sourceUrl, pipeCommand)
	ret0, _ := ret[0].(error)
	return ret0
}

// PipeData indicates an expected call of PipeData.
func (mr *MockServiceAdapterInterfaceMockRecorder) PipeData(ctx, sourceUrl, pipeCommand interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "PipeData", reflect.TypeOf((*MockServiceAdapterInterface)(nil).PipeData), ctx, sourceUrl, pipeCommand)
}

// Restart mocks base method.
func (m *MockServiceAdapterInterface) Restart(ctx context.Context) error {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "Restart", ctx)
	ret0, _ := ret[0].(error)
	return ret0
}

// Restart indicates an expected call of Restart.
func (mr *MockServiceAdapterInterfaceMockRecorder) Restart(ctx interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Restart", reflect.TypeOf((*MockServiceAdapterInterface)(nil).Restart), ctx)
}

// RunCmd mocks base method.
func (m *MockServiceAdapterInterface) RunCmd(ctx context.Context, cmd string, args []string) (string, error) {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "RunCmd", ctx, cmd, args)
	ret0, _ := ret[0].(string)
	ret1, _ := ret[1].(error)
	return ret0, ret1
}

// RunCmd indicates an expected call of RunCmd.
func (mr *MockServiceAdapterInterfaceMockRecorder) RunCmd(ctx, cmd, args interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "RunCmd", reflect.TypeOf((*MockServiceAdapterInterface)(nil).RunCmd), ctx, cmd, args)
}
