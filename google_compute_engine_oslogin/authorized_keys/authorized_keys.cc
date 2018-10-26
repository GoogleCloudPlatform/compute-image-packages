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

#include <iostream>
#include <sstream>
#include <string>

#include "../utils/oslogin_utils.h"

using std::cout;
using std::endl;
using std::string;

using oslogin_utils::HttpGet;
using oslogin_utils::ParseJsonToSuccess;
using oslogin_utils::ParseJsonToKey;
using oslogin_utils::ParseJsonToEmail;
using oslogin_utils::ParseJsonToSshKeys;
using oslogin_utils::UrlEncode;
using oslogin_utils::kMetadataServerUrl;

int main(int argc, char* argv[]) {
  if (argc != 2) {
    cout << "usage: authorized_keys [username]" << endl;
    return 1;
  }
  std::stringstream url;
  url << kMetadataServerUrl << "users?username=" << UrlEncode(argv[1]);
  string user_response;
  long http_code = 0;
  if (!HttpGet(url.str(), &user_response, &http_code) ||
      user_response.empty() || http_code != 200) {
    if (http_code == 404) {
      // Return 0 if the user is not an oslogin user. If we returned a failure
      // code, we would populate auth.log with useless error messages.
      return 0;
    }
    return 1;
  }
  string email;
  if (!ParseJsonToEmail(user_response, &email) || email.empty()) {
    return 1;
  }
  // Redundantly verify that this user has permission to log in to this VM.
  // Normally the PAM module determines this, but in the off chance a transient
  // error causes the PAM module to permit a user without login permissions,
  // perform the same check here. If this fails, we can guarantee that we won't
  // accidentally allow a user to log in without permissions.
  url.str("");
  url << kMetadataServerUrl << "authorize?email=" << UrlEncode(email)
      << "&policy=login";
  string auth_response;
  if (!HttpGet(url.str(), &auth_response, &http_code) || http_code != 200 ||
      auth_response.empty()) {
    return 1;
  }
  if (!ParseJsonToSuccess(auth_response)) {
    return 1;
  }
  // At this point, we've verified the user can log in. Grab the ssh keys from
  // the user response.
  std::vector<string> ssh_keys = ParseJsonToSshKeys(user_response);
  for (int i = 0; i < ssh_keys.size(); i++) {
    cout << ssh_keys[i] << endl;
  }
  return 0;
}
