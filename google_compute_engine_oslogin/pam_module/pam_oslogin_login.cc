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
#include <sstream>
#include <string>

#include "../utils/oslogin_utils.h"

using std::string;

using oslogin_utils::HttpGet;
using oslogin_utils::ParseJsonToAuthorizeResponse;
using oslogin_utils::ParseJsonToEmail;
using oslogin_utils::UrlEncode;
using oslogin_utils::kMetadataServerUrl;

extern "C" {

PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc,
                                const char **argv) {
  int pam_result = PAM_PERM_DENIED;
  const char *user_name;
  if ((pam_result = pam_get_user(pamh, &user_name, NULL)) != PAM_SUCCESS) {
    pam_syslog(pamh, LOG_INFO, "Could not get pam user.");
    return pam_result;
  }
  string str_user_name(user_name);

  std::stringstream url;
  url << kMetadataServerUrl << "users?username=" << UrlEncode(str_user_name);
  string response = HttpGet(url.str());
  if (response == "") {
    return PAM_SUCCESS;
  }
  string email = ParseJsonToEmail(response);
  if (email == "") {
    return PAM_SUCCESS;
  }

  url.str("");
  url << kMetadataServerUrl << "authorize?email=" << UrlEncode(email)
      << "&policy=login";
  response = HttpGet(url.str());
  if (ParseJsonToAuthorizeResponse(response)) {
    pam_syslog(pamh, LOG_INFO,
               "Granting login permission for organization user %s.",
               user_name);
    pam_result = PAM_SUCCESS;
  } else {
    pam_syslog(pamh, LOG_INFO,
               "Denying login permission for organization user %s.", user_name);
    pam_result = PAM_PERM_DENIED;
  }
  return pam_result;
}
}
