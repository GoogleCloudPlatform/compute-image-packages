// Copyright 2017 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#define PAM_SM_ACCOUNT
#include <security/pam_appl.h>
#include <security/pam_ext.h>
#include <security/pam_modules.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <syslog.h>
#include <unistd.h>

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

#include "../utils/oslogin_utils.h"

using std::string;

using oslogin_utils::HttpGet;
using oslogin_utils::ParseJsonToAuthorizeResponse;
using oslogin_utils::ParseJsonToEmail;
using oslogin_utils::UrlEncode;
using oslogin_utils::kMetadataServerUrl;

static const char kSudoersDir[] = "/var/google-sudoers.d/";

extern "C" {

PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc,
                                const char **argv) {
  // The return value for this module should generally be ignored. By default we
  // will return PAM_SUCCESS.
  int pam_result = PAM_SUCCESS;
  const char *user_name;
  if ((pam_result = pam_get_user(pamh, &user_name, NULL)) != PAM_SUCCESS) {
    pam_syslog(pamh, LOG_INFO, "Could not get pam user.");
    return pam_result;
  }
  string str_user_name(user_name);

  std::stringstream url;
  url << kMetadataServerUrl
      << "users?username=" << UrlEncode(str_user_name);
  string response;
  long http_code = 0;
  if (!HttpGet(url.str(), &response, &http_code) || http_code >= 400 ||
      response.empty()) {
    return PAM_SUCCESS;
  }
  string email = ParseJsonToEmail(response);
  if (email.empty()) {
    return PAM_SUCCESS;
  }

  url.str("");
  url << kMetadataServerUrl << "authorize?email=" << UrlEncode(email)
      << "&policy=adminLogin";

  string filename = kSudoersDir;
  filename.append(user_name);
  struct stat buffer;
  bool file_exists = !stat(filename.c_str(), &buffer);
  if (HttpGet(url.str(), &response, &http_code) && http_code == 200 &&
      ParseJsonToAuthorizeResponse(response)) {
    if (!file_exists) {
      pam_syslog(pamh, LOG_INFO,
                 "Granting sudo permissions to organization user %s.",
                 user_name);
      std::ofstream sudoers_file;
      sudoers_file.open(filename.c_str());
      sudoers_file << user_name << " ALL=(ALL) NOPASSWD: ALL"
                   << "\n";
      sudoers_file.close();
      chown(filename.c_str(), 0, 0);
      chmod(filename.c_str(), S_IRUSR | S_IWUSR | S_IRGRP);
    }
  } else if (file_exists) {
    remove(filename.c_str());
  }
  return pam_result;
}
}
