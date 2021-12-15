// Copyright 2021 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Implements dut_service.proto (see proto for details)
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"net/url"
	"path"
	"strings"
	"sync"

	"github.com/golang/protobuf/proto"
	"go.chromium.org/chromiumos/config/go/longrunning"
	"go.chromium.org/chromiumos/config/go/test/api"
	"golang.org/x/crypto/ssh"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"chromiumos/lro"
	"chromiumos/test/dut/cmd/cros-dut/dutssh"
	"chromiumos/test/dut/internal"
)

const CACHE_DOWNLOAD_URI = "/download/%s"
const CACHE_UNTAR_AND_DOWNLOAD_URI = "/extract/%s?file=%s"
const CACHE_EXTRACT_AND_DOWNLOAD_URI = "/decompress/%s"

// DutServiceServer implementation of dut_service.proto
type DutServiceServer struct {
	manager        *lro.Manager
	logger         *log.Logger
	connection     dutssh.ClientInterface
	serializerPath string
	protoChunkSize int64
	dutName        string
	wiringAddress  string
	cacheAddress   string
}

// newDutServiceServer creates a new dut service server to listen to rpc requests.
func newDutServiceServer(l net.Listener, logger *log.Logger, conn dutssh.ClientInterface, serializerPath string, protoChunkSize int64, dutName, wiringAddress string, cacheAddress string) (*grpc.Server, func()) {
	s := &DutServiceServer{
		manager:        lro.New(),
		logger:         logger,
		connection:     conn,
		serializerPath: serializerPath,
		protoChunkSize: protoChunkSize,
		dutName:        dutName,
		wiringAddress:  wiringAddress,
		cacheAddress:   cacheAddress,
	}

	server := grpc.NewServer()
	destructor := func() {
		s.connection.Close()
		s.manager.Close()
	}
	api.RegisterDutServiceServer(server, s)
	logger.Println("dutservice listen to request at ", l.Addr().String())
	return server, destructor
}

// Close closes DUT service.
func (s *DutServiceServer) Close() {
	s.manager.Close()
	s.connection.Close()
}

// ExecCommand remotely executes a command on the DUT.
func (s *DutServiceServer) ExecCommand(req *api.ExecCommandRequest, stream api.DutService_ExecCommandServer) error {
	s.logger.Println("Received api.ExecCommandRequest: ", *req)

	command := req.Command + " " + strings.Join(req.Args, " ")

	var stdin io.Reader = nil
	if len(req.Stdin) > 0 {
		stdin = bytes.NewReader(req.Stdin)

	}

	var combined bool = false
	if req.Stderr == api.Output_OUTPUT_STDOUT {
		combined = true
	}

	resp := s.runCmd(command, stdin, combined)
	return stream.Send(resp)
}

// FetchCrashes remotely fetches crashes from the DUT.
func (s *DutServiceServer) FetchCrashes(req *api.FetchCrashesRequest, stream api.DutService_FetchCrashesServer) error {
	s.logger.Println("Received api.FetchCrashesRequest: ", *req)
	if exists, err := s.runCmdOutput(dutssh.PathExistsCommand(s.serializerPath)); err != nil {
		return status.Errorf(codes.FailedPrecondition, "Failed to check crash_serializer existence: %s", err.Error())
	} else if exists != "1" {
		return status.Errorf(codes.NotFound, "crash_serializer not present on device.")
	}

	session, err := s.connection.NewSession()
	if err != nil {
		return status.Errorf(codes.FailedPrecondition, "Failed to start ssh session: %s", err)
	}
	defer session.Close()

	stdout, stderr, err := getPipes(session)
	if err != nil {
		return err
	}

	var wg sync.WaitGroup
	defer wg.Wait()

	wg.Add(1)
	// Grab stderr concurrently to reading the protos.
	go func() {
		defer wg.Done()

		for stderr.Scan() {
			log.Printf("crash_serializer: %s\n", stderr.Text())
		}
		if err := stderr.Err(); err != nil {
			log.Printf("Failed to get stderr: %s\n", err)
		}
	}()

	err = session.Start(dutssh.RunSerializerCommand(s.serializerPath, s.protoChunkSize, req.FetchCore))
	if err != nil {
		return status.Errorf(codes.FailedPrecondition, "Failed to run serializer: %s", err.Error())
	}

	var protoBytes bytes.Buffer

	for {
		crashResp, err := readFetchCrashesProto(stdout, protoBytes)
		if err != nil {
			return err
		} else if crashResp == nil {
			return nil
		}
		_ = stream.Send(crashResp)
	}
}

// Restart is a special case of ExecCommand which restarts the DUT and reconnects
func (s *DutServiceServer) Restart(ctx context.Context, req *api.RestartRequest) (*longrunning.Operation, error) {
	s.logger.Println("Received api.RestartRequest: ", *req)
	op := s.manager.NewOperation()

	command := "reboot " + strings.Join(req.Args, " ")
	output, err := s.runCmdOutput(command)
	if err != nil {
		return nil, err
	}

	s.manager.SetResult(op.Name, &api.RestartResponse{
		Output: output,
	})

	// Wait so following commands don't run before an actual reboot has kicked off
	// by waiting for the client connection to shutdown or a timeout.
	wait := make(chan interface{})
	go func() {
		_ = s.connection.Wait()
		close(wait)
	}()
	select {
	case <-wait:
		conn, err := GetConnection(ctx, s.dutName, s.wiringAddress)
		if err != nil {
			return nil, err
		}
		s.connection = &dutssh.SSHClient{Client: conn}

		return op, nil
	case <-ctx.Done():
		return nil, fmt.Errorf("rebootDUT: timeout waiting for reboot")
	}
}

// RunCmd implements the dutssh.CmdExecutor interface.
func (s *DutServiceServer) RunCmd(cmd string) (*dutssh.CmdResult, error) {
	resp := s.runCmd(cmd, nil, false)
	return &dutssh.CmdResult{
		ReturnCode: resp.ExitInfo.Status,
		StdOut:     string(resp.GetStdout()),
		StdErr:     string(resp.GetStderr()),
	}, nil
}

// DetectDeviceConfigId scans a live device and returns identity info.
func (s *DutServiceServer) DetectDeviceConfigId(
	req *api.DetectDeviceConfigIdRequest,
	stream api.DutService_DetectDeviceConfigIdServer) error {
	resp := internal.DetectDeviceConfigID(s)
	return stream.Send(resp)
}

// Cache downloads a specified file to the DUT via CacheForDut service
func (s *DutServiceServer) Cache(ctx context.Context, req *api.CacheRequest) (*longrunning.Operation, error) {
	s.logger.Println("Received api.CacheRequest: ", *req)
	op := s.manager.NewOperation()

	command := "curl -S -s -v -# -C - --retry 3 --retry-delay 60"

	destination, err := s.parseDestination(req)

	if err != nil {
		return nil, err
	}
	_, err = s.runCmdOutput(fmt.Sprintf("%s %s", command, destination))

	if err != nil {
		return nil, err
	} else {
		s.manager.SetResult(op.Name, &api.CacheResponse{
			Result: &api.CacheResponse_Success_{},
		})
	}

	return op, nil
}

func (s *DutServiceServer) parseDestination(req *api.CacheRequest) (string, error) {
	url, err := s.getCacheURL(req)
	if err != nil {
		return "", err
	}

	switch op := req.Destination.(type) {
	case *api.CacheRequest_File:
		// TODO(jaquesc): parse the file name to ensure it's a file and prevent user errors
		return fmt.Sprintf("-o %s %s", op.File.Path, url), nil
	case *api.CacheRequest_Pipe_:
		return fmt.Sprintf("%s | %s", url, op.Pipe.Commands), nil
	default:
		return "", fmt.Errorf("destination can only be one of LocalFile or Pipe")
	}
}

// getCacheURL returns a constructed URL to the caching service given a specific
// Source request type
func (s *DutServiceServer) getCacheURL(req *api.CacheRequest) (string, error) {
	switch op := req.Source.(type) {
	case *api.CacheRequest_GsFile:
		parsedPath, err := parseGSURL(op.GsFile.SourcePath)
		if err != nil {
			return "", err
		}
		return path.Join(s.cacheAddress, fmt.Sprintf(CACHE_DOWNLOAD_URI, parsedPath)), nil
	case *api.CacheRequest_GsTarFile:
		parsedPath, err := parseGSURL(op.GsTarFile.SourcePath)
		if err != nil {
			return "", err
		}
		return path.Join(s.cacheAddress, fmt.Sprintf(CACHE_UNTAR_AND_DOWNLOAD_URI, parsedPath, op.GsTarFile.SourceFile)), nil
	case *api.CacheRequest_GsZipFile:
		parsedPath, err := parseGSURL(op.GsZipFile.SourcePath)
		if err != nil {
			return "", err
		}
		return path.Join(s.cacheAddress, fmt.Sprintf(CACHE_EXTRACT_AND_DOWNLOAD_URI, parsedPath)), nil
	default:
		return "", fmt.Errorf("type can only be one of GsFile, GsTarFile or GSZipFile")
	}
}

// parseGSURL retrieves the bucket and object from a GS URL.
// URL expectation is of the form: "gs://bucket/object"
func parseGSURL(gsUrl string) (string, error) {
	if !strings.HasPrefix(gsUrl, "gs://") {
		return "", fmt.Errorf("gs url must begin with 'gs://', instead have, %s", gsUrl)
	}

	u, err := url.Parse(gsUrl)
	if err != nil {
		return "", fmt.Errorf("unable to parse url, %w", err)
	}

	// Host corresponds to bucket
	// Path corresponds to object
	return path.Join(u.Host, u.Path), nil
}

// ForceReconnect attempts to reconnect to the DUT
func (s *DutServiceServer) ForceReconnect(ctx context.Context, req *api.ForceReconnectRequest) (*longrunning.Operation, error) {
	s.logger.Println("Received api.ForceReconnectRequest: ", *req)

	op := s.manager.NewOperation()

	conn, err := GetConnection(ctx, s.dutName, s.wiringAddress)

	if err != nil {
		return nil, err
	} else {
		s.manager.SetResult(op.Name, &api.CacheResponse{
			Result: &api.CacheResponse_Success_{},
		})

	}

	s.connection = &dutssh.SSHClient{Client: conn}

	return op, nil
}

// readFetchCrashesProto reads stdout and transforms it into a FetchCrashesResponse
func readFetchCrashesProto(stdout io.Reader, buffer bytes.Buffer) (*api.FetchCrashesResponse, error) {
	var sizeBytes [8]byte
	crashResp := &api.FetchCrashesResponse{}

	buffer.Reset()

	// First, read the length of the proto.
	length, err := io.ReadFull(stdout, sizeBytes[:])
	if err != nil {
		if length == 0 && err == io.EOF {
			// We've come to the end of the stream -- expected condition.
			return nil, nil
		}
		// Read only a partial int. Abort.
		return nil, status.Errorf(codes.Unavailable, "Failed to read a size: %s", err.Error())
	}
	size := binary.BigEndian.Uint64(sizeBytes[:])

	// Next, read the actual proto and parse it.
	if length, err := io.CopyN(&buffer, stdout, int64(size)); err != nil {
		return nil, status.Errorf(codes.Unavailable, "Failed to read complete proto. Read %d bytes but wanted %d. err: %s", length, size, err)
	}
	// CopyN guarantees that n == protoByes.Len() == size now.

	if err := proto.Unmarshal(buffer.Bytes(), crashResp); err != nil {
		return nil, status.Errorf(codes.Internal, "Failed to unmarshal proto: %s; %v", err.Error(), buffer.Bytes())
	}

	return crashResp, nil
}

// GetConnection connects to a dut server. If wiringAddress is provided,
// it resolves the dut name to ip address; otherwise, uses dutIdentifier as is.
func GetConnection(ctx context.Context, dutIdentifier string, wiringAddress string) (*ssh.Client, error) {
	var addr string
	if wiringAddress != "" {
		var err error
		addr, err = dutssh.GetSSHAddr(ctx, dutIdentifier, wiringAddress)
		if err != nil {
			return nil, err
		}
	} else {
		addr = dutIdentifier
	}

	return ssh.Dial("tcp", addr, dutssh.GetSSHConfig())
}

// runCmd run remote command returning return value, stdout, stderr, and error if any
func (s *DutServiceServer) runCmd(cmd string, stdin io.Reader, combined bool) *api.ExecCommandResponse {
	session, err := s.connection.NewSession()
	if err != nil {
		return &api.ExecCommandResponse{
			ExitInfo: createFailedToStartExitInfo(err),
		}
	}
	defer session.Close()

	var stdOut bytes.Buffer
	var stdErr bytes.Buffer

	if stdin != nil {
		session.SetStdin(stdin)
	}
	session.SetStdout(&stdOut)
	if !combined {
		session.SetStderr(&stdErr)
	} else {
		session.SetStderr(&stdOut)
	}
	err = session.Run(cmd)

	return &api.ExecCommandResponse{
		Stdout:   stdOut.Bytes(),
		Stderr:   stdErr.Bytes(),
		ExitInfo: getExitInfo(err),
	}
}

// runCmdOutput interprets the given string command in a shell and returns stdout.
// Overall this is a simplified version of runCmd which only returns output.
func (s *DutServiceServer) runCmdOutput(cmd string) (string, error) {
	session, err := s.connection.NewSession()
	if err != nil {
		return "", err
	}
	defer session.Close()
	b, err := session.Output(cmd)
	return string(b), err
}

// getExitInfo extracts exit info from Session Run's error
func getExitInfo(runError error) *api.ExecCommandResponse_ExitInfo {
	// If no error, command succeeded
	if runError == nil {
		return createCommandSucceededExitInfo()
	}

	// If ExitError, command ran but did not succeed
	var ee *ssh.ExitError
	if errors.As(runError, &ee) {
		return createCommandFailedExitInfo(ee)
	}

	// Otherwise we assume command failed to start
	return createFailedToStartExitInfo(runError)
}

func createFailedToStartExitInfo(err error) *api.ExecCommandResponse_ExitInfo {
	return &api.ExecCommandResponse_ExitInfo{
		Status:       42, // Contract dictates arbitrary response, thus 42 is as good as any number
		Signaled:     false,
		Started:      false,
		ErrorMessage: err.Error(),
	}
}

func createCommandSucceededExitInfo() *api.ExecCommandResponse_ExitInfo {
	return &api.ExecCommandResponse_ExitInfo{
		Status:       0,
		Signaled:     false,
		Started:      true,
		ErrorMessage: "",
	}
}

func createCommandFailedExitInfo(err *ssh.ExitError) *api.ExecCommandResponse_ExitInfo {
	return &api.ExecCommandResponse_ExitInfo{
		Status:       int32(err.ExitStatus()),
		Signaled:     true,
		Started:      true,
		ErrorMessage: "",
	}
}

// getPipes returns stdout and stderr from a Session/SessionInterface. stderr is
// converted to a buffer do to concurrency expectations
func getPipes(s dutssh.SessionInterface) (io.Reader, *bufio.Scanner, error) {
	stdout, err := s.StdoutPipe()
	if err != nil {
		return nil, nil, status.Errorf(codes.FailedPrecondition, "Failed to get stdout: %s", err)
	}

	stderrReader, err := s.StderrPipe()
	if err != nil {
		return nil, nil, status.Errorf(codes.FailedPrecondition, "Failed to get stderr: %s", err)
	}
	stderr := bufio.NewScanner(stderrReader)

	return stdout, stderr, nil
}
