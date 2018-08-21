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
#include <security/pam_modules.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <syslog.h>
#include <unistd.h>

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <map>

#include "../compat.h"
#include "../utils/oslogin_utils.h"

using std::string;

using oslogin_utils::ContinueSession;
using oslogin_utils::GetUser;
using oslogin_utils::HttpGet;
using oslogin_utils::HttpPost;
using oslogin_utils::kMetadataServerUrl;
using oslogin_utils::ParseJsonToChallenges;
using oslogin_utils::ParseJsonToKey;
using oslogin_utils::ParseJsonToEmail;
using oslogin_utils::ParseJsonToSuccess;
using oslogin_utils::StartSession;
using oslogin_utils::UrlEncode;
using oslogin_utils::ValidateUserName;

static const char kUsersDir[] = "/var/google-users.d/";

extern "C" {

PAM_EXTERN int pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc,
                                const char **argv) {
  int pam_result = PAM_PERM_DENIED;
  const char *user_name;
  if ((pam_result = pam_get_user(pamh, &user_name, NULL)) != PAM_SUCCESS) {
    PAM_SYSLOG(pamh, LOG_INFO, "Could not get pam user.");
    return pam_result;
  }
  string str_user_name(user_name);
  if (!ValidateUserName(user_name)) {
    // If the user name is not a valid oslogin user, don't bother continuing.
    return PAM_SUCCESS;
  }
  string users_filename = kUsersDir;
  users_filename.append(user_name);
  struct stat buffer;
  bool file_exists = !stat(users_filename.c_str(), &buffer);

  std::stringstream url;
  url << kMetadataServerUrl << "users?username=" << UrlEncode(str_user_name);
  string response;
  long http_code = 0;
  if (!HttpGet(url.str(), &response, &http_code) || response.empty() ||
      http_code != 200) {
    if (http_code == 404) {
      // Return success on non-oslogin users.
      return PAM_SUCCESS;
    }
    // If we can't reliably tell if this is an oslogin user, check if there is
    // a local file for that user as a last resort.
    if (file_exists) {
      return PAM_PERM_DENIED;
    }
    // Otherwise, fall back on success to allow local users to log in.
    return PAM_SUCCESS;
  }

  string email;
  if (!ParseJsonToEmail(response, &email) || email.empty()) {
    return PAM_PERM_DENIED;
  }

  url.str("");
  url << kMetadataServerUrl << "authorize?email=" << UrlEncode(email)
      << "&policy=login";
  if (HttpGet(url.str(), &response, &http_code) && http_code == 200 &&
      ParseJsonToSuccess(response)) {
    if (!file_exists) {
      std::ofstream users_file(users_filename.c_str());
      chown(users_filename.c_str(), 0, 0);
      chmod(users_filename.c_str(), S_IRUSR | S_IWUSR | S_IRGRP);
    }
    PAM_SYSLOG(pamh, LOG_INFO,
               "Granting login permission for organization user %s.",
               user_name);
    pam_result = PAM_SUCCESS;
  } else {
    if (file_exists) {
      remove(users_filename.c_str());
    }
    pam_syslog(pamh, LOG_INFO,
               "Denying login permission for organization user %s.",
               user_name);

    pam_result = PAM_PERM_DENIED;
  }
  return pam_result;
}
PAM_EXTERN int pam_sm_setcred(pam_handle_t * pamh, int flags, int argc,
                              const char **argv)
{
  return PAM_SUCCESS;
}


PAM_EXTERN int pam_sm_authenticate(pam_handle_t * pamh, int flags,
                                   int argc, const char **argv)
{
  const char* user_name;
  if (pam_get_user(pamh, &user_name, NULL) != PAM_SUCCESS) {
    pam_syslog(pamh, LOG_INFO, "Could not get pam user.");
    return PAM_PERM_DENIED;
  }

  string str_user_name(user_name);
  if (!ValidateUserName(user_name)) {
    return PAM_PERM_DENIED;
  }

  string response;
  if (!(GetUser(str_user_name, &response))) {
    return PAM_PERM_DENIED;
  }

  // System accounts begin with the prefix `sa_`.
  string sa_prefix = "sa_";
  if (str_user_name.compare(0, sa_prefix.size(), sa_prefix) == 0) {
    return PAM_SUCCESS;
  }

  string email;
  if (!ParseJsonToEmail(response, &email) || email.empty()) {
    return PAM_PERM_DENIED;
  }

  response = "";
  if (!StartSession(email, &response)) {
    pam_syslog(pamh, LOG_ERR,
               "Bad response from the two-factor start session request: %s",
               response.empty() ? "empty response" : response.c_str());
    return PAM_PERM_DENIED;
  }

  string status;
  if (!ParseJsonToKey(response, "status", &status)) {
    pam_syslog(pamh, LOG_ERR,
               "Failed to parse status from start session response");
    return PAM_PERM_DENIED;
  }

  if (status == "NO_AVAILABLE_CHALLENGES") {
    return PAM_SUCCESS; // User is not two-factor enabled.
  }

  string session_id;
  if (!ParseJsonToKey(response, "sessionId", &session_id)) {
    return PAM_PERM_DENIED;
  }

  std::vector<oslogin_utils::Challenge> challenges;
  if (!ParseJsonToChallenges(response, &challenges)) {
    pam_syslog(pamh, LOG_ERR,
               "Failed to parse challenge values from JSON response");
    return PAM_PERM_DENIED;
  }

  std::map<string,string> user_prompts;
  user_prompts[AUTHZEN] = "Google phone prompt";
  user_prompts[TOTP] = "Security code from Google Authenticator application";
  user_prompts[INTERNAL_TWO_FACTOR] = "Security code from security key";
  user_prompts[IDV_PREREGISTERED_PHONE] = 
      "Voice or text message verification code";

  oslogin_utils::Challenge challenge;
  if (challenges.size() > 1) {
    std::stringstream prompt;
    prompt << "Available authentication methods: ";
    for(vector<oslogin_utils::Challenge>::size_type i = 0;
        i != challenges.size(); ++i)
      prompt << "\n" << i+1 << ": " << user_prompts[challenges[i].type];
    prompt << "\n\nEnter a number: ";

    char *choice = NULL;
    if (pam_prompt(pamh, PAM_PROMPT_ECHO_ON, &choice, "%s",
                   prompt.str().c_str()) != PAM_SUCCESS) {
      pam_error(pamh, "Unable to get user input");
    }

    int choicei;
    if (sscanf(choice, "%d", &choicei) == EOF) {
      pam_error(pamh, "Unable to get user input");
    }
    if (choicei > challenges.size()) {
      pam_error(pamh, "Invalid option");
    }
    challenge = challenges[choicei - 1];
  } else {
    challenge = challenges[0];
  }

  char* user_token = NULL;
  if (challenge.type == INTERNAL_TWO_FACTOR) {
    if (pam_prompt(pamh, PAM_PROMPT_ECHO_ON, &user_token,
                   "Enter your security code: ") != PAM_SUCCESS) {
      pam_error(pamh, "Unable to get user input");
    }
  } else if (challenge.type == TOTP) {
    if (pam_prompt(pamh, PAM_PROMPT_ECHO_ON, &user_token,
                   "Enter your one-time password: ") != PAM_SUCCESS) {
      pam_error(pamh, "Unable to get user input");
    }
  } else if (challenge.type == AUTHZEN) {
    if (pam_prompt(pamh, PAM_PROMPT_ECHO_ON, &user_token,
                   "A login prompt has been sent to your enrolled device. "
                   "Press enter to continue") != PAM_SUCCESS) {
      pam_error(pamh, "Unable to get user input");
    }
  } else if (challenge.type == IDV_PREREGISTERED_PHONE) {
    if (pam_prompt(pamh, PAM_PROMPT_ECHO_ON, &user_token,
                   "A security code has been sent to your phone. "
                   "Enter code to continue: ") != PAM_SUCCESS) {
      pam_error(pamh, "Unable to get user input");
    }
  } else {
    pam_syslog(pamh, LOG_ERR, "Unsupported challenge type %s",
               challenge.type.c_str());
    return PAM_PERM_DENIED;
  }

  if (!ContinueSession(email, user_token, session_id, challenge, &response)) {
      pam_syslog(pamh, LOG_ERR,
                 "Bad response from two-factor continue session request: %s",
                 response.empty() ? "empty response" : response.c_str());
      return PAM_PERM_DENIED;
  }

  if (!ParseJsonToKey(response, "status", &status)
      || status != "AUTHENTICATED") {
    return PAM_PERM_DENIED;
  }

  return PAM_SUCCESS;
}
}
