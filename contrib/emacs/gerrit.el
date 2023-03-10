;; -*- lexical-binding: t -*-

;; Copyright 2020 The Chromium OS Authors. All rights reserved.
;; Use of this source code is governed by a BSD-style license that can be
;; found in the LICENSE file.
(require 'request)
(require 'xml)


(defcustom gerrit-repo-root
  nil
  "The system path to the repo project root."
  :type 'string)

(defcustom gerrit-git-cookies
  (expand-file-name ".gitcookies" "~/")
  "Path to gitcookies associated with your Gerrit account."
  :type 'string)

(defcustom gerrit-hosts
  ;; TODO extract this variable from the
  ;; repo manifest instead of user configuration.
  nil
  "Gerrit hosts you're interested in reviewing comments."
  :type '(string))

(defcustom gerrit-curl-exec
  "curl"
  "The curl-like executable for making requests to Gerrit.
Defaults to curl."
  :type 'string)

(defconst gerrit--manifest-parser
  (expand-file-name
   "manifest_parser"
   (file-name-directory load-file-name))
  "The executable used to parse the repo manifest as an alist.")


(defvar gerrit--change-to-host
  (make-hash-table :test 'equal)
  "Map showing => host.
Needed for generating links.")


(defun gerrit-init ()
  "Initialize Repo Gerrit state."
  ;; If using cURL use special options.
  ;; Authenticate using cURL with gitcookies.
  ;; Use let to shadow dynamic scoped var to avoid
  ;; side effects with other users of request.el
  (let ((request-curl gerrit-curl-exec)
        (request-curl-options
         (unless (string-suffix-p "gob-curl" gerrit-curl-exec)
           ;; Follow links and use git cookies.
           `("-Lb" ,gerrit-git-cookies))))

    (gerrit--init-global-comment-map)
    (gerrit--init-global-repo-project-path-map gerrit--manifest-parser
                                               gerrit-repo-root)))


(defvar gerrit--change-to-filepath-comments nil
  "Map containing with change => filepath => comments.
filepath is from git project root, for the given change.")


(defvar gerrit--project-branch-pair-to-projectpath nil
  "Map showing relative path from repo root to project.
Is of the form (project . dest-branch) => path-from-repo-root.")


(cl-defun gerrit--fetch-recent-changes (host &optional (count 3))
  "Fetches recent changes as ChangeInfo entities.
host - Gerrit server address
count (optional) - the number of recent changes, default is 3
Fetch recent changes that are not abandoned/merged, and
thus are actionable, returns an array of hashtables that
represent Gerrit ChangeInfo entities."
  (request-response-data
   (request
     (format "https://%s/a/changes/" host)
     ;; We don't use "status:reviewed" because that
     ;; only counts reviews after latest patch,
     ;; but we may want reviews before the latest patch too.
     :params `(("q" . "owner:self status:open")
               ("n" . ,(format "%d" count)))
     :sync t
     :parser 'gerrit--request-response-json-parser)))


(defun gerrit--request-response-json-parser ()
  "Response parsing callback for use with request.el
parses Gerrit response json payload by removing the
embedded XSS protection string before using a real json parser."
  (json-parse-string (replace-regexp-in-string "^[[:space:]]*)]}'" "" (buffer-string))))


(defun gerrit--fetch-comments (host change)
  "Gets recent comments for open Gerrit CLs.
Returns a map of the form path => sequence of comments,
where path is the filepath from the gerrit project root
and each comment represents a CommentInfo entity from Gerrit"
  (request-response-data
   (request
     (format "https://%s/a/changes/%s~master~%s/comments"
             host
             (url-hexify-string (gethash "project" change))
             (gethash "change_id" change))
     :sync t
     :parser 'gerrit--request-response-json-parser)))


(defun gerrit--fetch-change-to-file-to-comments ()
  "Returns a map of maps of the form:
change => filepath => array(CommentInfo Map),
where filepath is from the nearest git root for a file.
Only fetches recent changes for open CLs."
  (let ((out-map (make-hash-table :test 'equal)))
    (loop for host in gerrit-hosts do
          (loop for change across (gerrit--fetch-recent-changes host) do
                (setf (gethash (gethash "change_id" change)
                               gerrit--change-to-host)
                      host)
                (setf (gethash change out-map)
                      (gerrit--fetch-comments host change))))
    out-map))


(defun gerrit--init-global-comment-map ()
  "Inits `gerrit--change-to-filepath-comments`."
  (setf gerrit--change-to-filepath-comments
        (gerrit--fetch-change-to-file-to-comments)))


(cl-defun gerrit--project-branch-pair-to-path-map (path-to-manifest-parser-exec
                                                   path-to-repo-root)
  "Return map (project . dest-branch) => path-from-repo-root.
Parses the repo manifest using the given parser executable.
Assumes that stdout of parser is a Lisp alist of the form:
((project . dest-branch) . path-from-repo-root)."
  (let (parsed-alist
        (output (make-hash-table :test 'equal))
        (tmp-buffer-name "*gerrit-temp--buffer*"))

    (when (get-buffer tmp-buffer-name)
      (kill-buffer tmp-buffer-name))

    (unless (= 0 (call-process path-to-manifest-parser-exec
                               nil
                               tmp-buffer-name
                               nil
                               path-to-repo-root))
      (message "Error parsing manifest investigate %s" tmp-buffer-name)
      (cl-return-from gerrit--project-branch-pair-to-path-map nil))

    (save-excursion
      (set-buffer tmp-buffer-name)
      (goto-char (point-min))
      (setf parsed-alist (read (current-buffer)))
      (kill-buffer tmp-buffer-name))

    (loop for item in parsed-alist do
          (setf (gethash (car item) output) (cdr item)))

    output))


(defun gerrit--init-global-repo-project-path-map (path-to-manifest-parser-exec
                                                  path-to-repo-root)
  "Initializes `gerrit--project-branch-pair-to-projectpath`.
This function is idempotent."
  ;; Here we use Python expat sax parser as it's considerably faster.
  (unless gerrit--project-branch-pair-to-projectpath
    (setf gerrit--project-branch-pair-to-projectpath
          (gerrit--project-branch-pair-to-path-map
           path-to-manifest-parser-exec
           path-to-repo-root))))


(defun gerrit--get-abs-path-to-file (filepath-from-project-git-root
                                     project-branch-pair
                                     path-to-repo-root)
  "Returns full system path of the first argument.
`gerrit--project-branch-pair-to-projectpath` must be initialized."
  (expand-file-name
   filepath-from-project-git-root
   (directory-file-name
    (expand-file-name
     (gethash (cons (gethash "project" project-branch-pair)
                    (gethash "branch" project-branch-pair))
              gerrit--project-branch-pair-to-projectpath)
     path-to-repo-root))))


(provide 'gerrit)
(require 'gerrit)
