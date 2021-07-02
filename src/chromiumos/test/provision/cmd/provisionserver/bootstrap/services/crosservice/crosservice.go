// Copyright 2021 The Chromium OS Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// CrOSInstall state machine construction and helper
package crosservice

import (
	"chromiumos/test/provision/cmd/provisionserver/bootstrap/info"
	"chromiumos/test/provision/cmd/provisionserver/bootstrap/services"
	"context"
	"fmt"
	"log"
	"path"
	"regexp"
	"strings"

	conf "go.chromium.org/chromiumos/config/go"
	"go.chromium.org/chromiumos/config/go/test/api"
	"google.golang.org/grpc"
)

// CrOSService inherits ServiceInterface
type CrOSService struct {
	connection        services.ServiceAdapterInterface
	imagePath         *conf.StoragePath
	preserverStateful bool
	dlcSpecs          []*api.InstallCrosRequest_DLCSpec
}

func NewCrOSService(dutName string, dutClient api.DutServiceClient, wiringConn *grpc.ClientConn, req *api.InstallCrosRequest) CrOSService {
	return CrOSService{
		connection:        services.NewServiceAdapter(dutName, dutClient, wiringConn),
		imagePath:         req.CrosImagePath,
		preserverStateful: req.PreserveStateful,
		dlcSpecs:          req.DlcSpecs,
	}
}

// NewCrOSServiceFromExistingConnection is equivalent to the obove constructor,
// but recycles a ServiceAdapter. Generally useful for tests.
func NewCrOSServiceFromExistingConnection(conn services.ServiceAdapterInterface, imagePath *conf.StoragePath, preserverStateful bool, dlcSpecs []*api.InstallCrosRequest_DLCSpec) CrOSService {
	return CrOSService{
		connection:        conn,
		imagePath:         imagePath,
		preserverStateful: preserverStateful,
		dlcSpecs:          dlcSpecs,
	}
}

// GetFirstState returns the first state of this state machine
func (c *CrOSService) GetFirstState() services.ServiceState {
	return CrOSInstallState{
		service: *c,
	}
}

/*
	The following run specific commands related to CrOS installation.
*/

// GetRoot returns the rootdev outoput for root
func (c *CrOSService) GetRoot(ctx context.Context) (string, error) {
	// Example 1: "/dev/nvme0n1p3"
	// Example 2: "/dev/sda3"
	curRoot, err := c.connection.RunCmd(ctx, "rootdev", []string{"-s"})
	if err != nil {
		return "", fmt.Errorf("failed to get current root, %s", err)
	}
	return strings.TrimSpace(curRoot), nil
}

// GetRootDisk returns the rootdev output for disk
func (c *CrOSService) GetRootDisk(ctx context.Context) (string, error) {
	// Example 1: "/dev/nvme0n1"
	// Example 2: "/dev/sda"
	rootDisk, err := c.connection.RunCmd(ctx, "rootdev", []string{"-s", "-d"})
	if err != nil {
		return "", fmt.Errorf("failed to get root disk, %s", err)
	}
	return strings.TrimSpace(rootDisk), nil
}

// GetRootPartNumber parses the root number for a specific root
func (c *CrOSService) GetRootPartNumber(ctx context.Context, root string) (string, error) {
	// Handle /dev/mmcblk0pX, /dev/sdaX, etc style partitions.
	// Example 1: "3"
	// Example 2: "3"
	match := regexp.MustCompile(`.*([0-9]+)`).FindStringSubmatch(root)
	if match == nil {
		return "", fmt.Errorf("failed to match partition number from %s", root)
	}

	switch match[1] {
	case info.PartitionNumRootA, info.PartitionNumRootB:
		break
	default:
		return "", fmt.Errorf("invalid partition number %s", match[1])
	}

	return match[1], nil
}

// stopSystemDaemon stops system daemons than can interfere with provisioning.
func (c *CrOSService) StopSystemDaemons(ctx context.Context) error {
	if _, err := c.connection.RunCmd(ctx, "stop", []string{"ui"}); err != nil {
		return fmt.Errorf("failed to stop UI daemon, %s", err)
	}
	if _, err := c.connection.RunCmd(ctx, "stop", []string{"update-engine"}); err != nil {
		return fmt.Errorf("failed to stop update-engine daemon, %s", err)
	}
	return nil
}

// ClearDLCArtifacts will clear the verified marks for all DLCs in the inactive slots.
func (c *CrOSService) ClearDLCArtifacts(ctx context.Context, rootPartNum string) error {
	exists, err := c.connection.PathExists(ctx, info.DlcLibDir)
	if err != nil {
		return fmt.Errorf("failed path existance, %s", err)
	}
	if !exists {
		return fmt.Errorf("DLC path does not exist")
	}

	// Stop dlcservice daemon in order to not interfere with clearing inactive verified DLCs.
	if _, err := c.connection.RunCmd(ctx, "stop", []string{"dlcservice"}); err != nil {
		log.Printf("clear DLC artifacts: failed to stop dlcservice daemon, %s", err)
	}
	defer func() {
		if _, err := c.connection.RunCmd(ctx, "start", []string{"dlcservice"}); err != nil {
			log.Printf("clear DLC artifacts: failed to start dlcservice daemon, %s", err)
		}
	}()

	inactiveSlot := info.InactiveDlcMap[rootPartNum]
	if inactiveSlot == "" {
		return fmt.Errorf("invalid root partition number: %s", rootPartNum)
	}
	_, err = c.connection.RunCmd(ctx, "rm", []string{"-f", path.Join(info.DlcCacheDir, "*", "*", string(inactiveSlot), info.DlcVerified)})
	if err != nil {
		return fmt.Errorf("failed remove inactive verified DLCs, %s", err)
	}

	return nil
}

// InstallPartitions  installs the kernel and root images in parallel
func (c *CrOSService) InstallPartitions(ctx context.Context, pi info.PartitionInfo) []error {
	kernelErr := make(chan error)
	rootErr := make(chan error)
	go func() {
		// Install Kernel
		kernelErr <- c.InstallZippedImage(ctx, "full_dev_part_KERN.bin.gz", pi.InactiveKernel)
	}()
	go func() {
		// Install Root
		rootErr <- c.InstallZippedImage(ctx, "full_dev_part_ROOT.bin.gz", pi.InactiveRoot)
	}()

	var provisionErrs []error
	if err := <-kernelErr; err != nil {
		provisionErrs = append(provisionErrs, err)
	}
	if err := <-rootErr; err != nil {
		provisionErrs = append(provisionErrs, err)
	}
	return provisionErrs
}

// InstallZippedImage installs a remote zipped image to disk.
func (c *CrOSService) InstallZippedImage(ctx context.Context, remoteImagePath string, outputFile string) error {
	if c.imagePath.HostType == conf.StoragePath_LOCAL || c.imagePath.HostType == conf.StoragePath_HOSTTYPE_UNSPECIFIED {
		return fmt.Errorf("only GS copying is implemented")
	}
	url, err := c.connection.CopyData(ctx, path.Join(c.imagePath.GetPath(), remoteImagePath))
	if err != nil {
		return fmt.Errorf("failed to get GS Cache URL, %s", err)
	}
	_, err = c.connection.RunCmd(ctx, "curl", []string{url, "|", "gzip -d", "|", fmt.Sprintf("dd of=%s obs=2M", outputFile)})
	return err
}

// PostInstall mounts and runs post installation items.
func (c *CrOSService) PostInstall(ctx context.Context, inactiveRoot string) error {
	_, err := c.connection.RunCmd(ctx, "", []string{
		"tmpmnt=$(mktemp -d)",
		"&&",
		fmt.Sprintf("mount -o ro %s ${tmpmnt}", inactiveRoot),
		"&&",
		fmt.Sprintf("${tmpmnt}/postinst %s", inactiveRoot),
		"&&",
		"{ umount ${tmpmnt} || true; }",
		"&&",
		"{ rmdir ${tmpmnt} || true; }",
	})
	return err
}

// ClearTPM runs crosssystem clear tpm request
func (c *CrOSService) ClearTPM(ctx context.Context) error {
	_, err := c.connection.RunCmd(ctx, "crossystem", []string{"clear_tpm_owner_request=1"})
	return err
}

// RevertStatefulInstall literally reverses a stateful installation
func (c *CrOSService) RevertStatefulInstall(ctx context.Context) {
	varNewPath := path.Join(info.StatefulPath, "var_new")
	devImageNewPath := path.Join(info.StatefulPath, "dev_image_new")
	_, err := c.connection.RunCmd(ctx, "rm", []string{"-rf", varNewPath, devImageNewPath, info.UpdateStatefulFilePath})
	if err != nil {
		log.Printf("revert stateful install: failed to revert stateful installation, %s", err)
	}
}

// RevertPostInstall literally reverses a PostInstall
func (c *CrOSService) RevertPostInstall(ctx context.Context, activeRoot string) {
	if _, err := c.connection.RunCmd(ctx, "/postinst", []string{activeRoot, "2>&1"}); err != nil {
		log.Printf("revert post install: failed to revert postinst, %s", err)
	}
}

// RevertProvisionOS literally reverts a full OS provisioning
func (c *CrOSService) RevertProvisionOS(ctx context.Context, activeRoot string) {
	c.RevertStatefulInstall(ctx)
	c.RevertPostInstall(ctx, activeRoot)
}

// WipeStateful removes all things relevant to a stateful install
func (c *CrOSService) WipeStateful(ctx context.Context) error {
	if _, err := c.connection.RunCmd(ctx, "echo", []string{"'fast keepimg'", ">", "/mnt/stateful_partition/factory_install_reset"}); err != nil {
		return fmt.Errorf("failed to to write to factory reset file, %s", err)
	}
	return nil
}

// Provision stateful runs a stateful install, reverting if it fails.
func (c *CrOSService) ProvisionStateful(ctx context.Context) error {
	c.StopSystemDaemons(ctx)

	if err := c.InstallStateful(ctx); err != nil {
		c.RevertStatefulInstall(ctx)
		return fmt.Errorf("failed to install stateful partition, %s", err)
	}
	return nil
}

// InstallStateful updates the stateful partition on disk (finalized after a reboot).
func (c *CrOSService) InstallStateful(ctx context.Context) error {
	if c.imagePath.HostType == conf.StoragePath_LOCAL || c.imagePath.HostType == conf.StoragePath_HOSTTYPE_UNSPECIFIED {
		return fmt.Errorf("only GS copying is implemented")
	}
	url, err := c.connection.CopyData(ctx, path.Join(c.imagePath.GetPath(), "stateful.tzg"))
	if err != nil {
		return fmt.Errorf("failed to get GS Cache URL, %s", err)
	}
	_, err = c.connection.RunCmd(ctx, "", []string{
		fmt.Sprintf("rm -rf %[1]s %[2]s/var_new %[2]s/dev_image_new", info.UpdateStatefulFilePath, info.StatefulPath),
		"&&",
		fmt.Sprintf("curl %s | tar --ignore-command-error --overwrite --directory=%s -xzf -", url, info.StatefulPath),
		"&&",
		fmt.Sprintf("echo -n clobber > %s", info.UpdateStatefulFilePath),
	})
	return err
}

// StopDLCService stops a DLC service
func (c *CrOSService) StopDLCService(ctx context.Context) {
	if _, err := c.connection.RunCmd(ctx, "stop", []string{"dlcservice"}); err != nil {
		log.Printf("failed to stop dlcservice daemon, %s", err)
	}
}

// StopDLCService starts a DLC service
func (c *CrOSService) StartDLCService(ctx context.Context) {
	if _, err := c.connection.RunCmd(ctx, "start", []string{"dlcservice"}); err != nil {
		log.Printf("failed to start dlcservice daemon, %s", err)
	}
}

// InstallDLC installs all relevant DLCs
func (c *CrOSService) InstallDLC(ctx context.Context, spec *api.InstallCrosRequest_DLCSpec, slot string) error {
	dlcID := spec.GetId()
	dlcOutputDir := path.Join(info.DlcCacheDir, dlcID, info.DlcPackage)
	verified, err := c.IsDLCVerified(ctx, spec.GetId(), slot)
	if err != nil {
		return fmt.Errorf("failed is DLC verified check, %s", err)
	}

	// Skip installing the DLC if already verified.
	if verified {
		log.Printf("provision DLC %s skipped as already verified", dlcID)
		return nil
	}

	if c.imagePath.HostType == conf.StoragePath_LOCAL || c.imagePath.HostType == conf.StoragePath_HOSTTYPE_UNSPECIFIED {
		return fmt.Errorf("only GS copying is implemented")
	}
	dlcURL := path.Join(c.imagePath.GetPath(), "dlc", dlcID, info.DlcPackage, info.DlcImage)
	url, err := c.connection.CopyData(ctx, dlcURL)
	if err != nil {
		return fmt.Errorf("failed to get GS Cache server, %s", err)
	}

	dlcOutputSlotDir := path.Join(dlcOutputDir, string(slot))
	dlcOutputImage := path.Join(dlcOutputSlotDir, info.DlcImage)
	if _, err := c.connection.RunCmd(ctx, "", []string{
		"mkdir", "-p", dlcOutputSlotDir,
		"&&",
		"curl", "--output", dlcOutputImage, url,
	}); err != nil {
		return fmt.Errorf("failed to provision DLC %s, %s", dlcID, err)
	}
	return nil
}

// IsDLCVerified checks if the desired DLC already exists within the system
func (c *CrOSService) IsDLCVerified(ctx context.Context, dlcID, slot string) (bool, error) {
	verified, err := c.connection.PathExists(ctx, path.Join(info.DlcLibDir, dlcID, slot, info.DlcVerified))
	if err != nil {
		return false, fmt.Errorf("failed to check if DLC %s is verified, %s", dlcID, err)
	}
	return verified, nil
}