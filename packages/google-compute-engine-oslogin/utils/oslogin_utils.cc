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

// Requires libcurl4-openssl-dev libjson0 and libjson0-dev
#include <curl/curl.h>
#include <errno.h>
#include <json.h>
#include <nss.h>
#include <stdio.h>
#include <time.h>
#include <cstring>
#include <iostream>
#include <sstream>

#ifdef __GNUC__
#if __GNUC__ > 4 || \
  (__GNUC__ == 4 && (__GNUC_MINOR__ > 9 || \
                     (__GNUC_MINOR__ == 9 && \
                      __GNUC_PATCHLEVEL__ > 0)))
#include <regex>
#define Regex std
#else
#include <boost/regex.hpp>
#define Regex boost
#endif
#endif

#include "oslogin_utils.h"
#include "../compat.h"

using std::string;

// Maximum number of retries for HTTP requests.
const int kMaxRetries = 1;

// Regex for validating user names.
const char kUserNameRegex[] = "^[a-zA-Z0-9._][a-zA-Z0-9._-]{0,31}$";

namespace oslogin_utils {

BufferManager::BufferManager(char* buf, size_t buflen)
    : buf_(buf), buflen_(buflen) {}

bool BufferManager::AppendString(const string& value, char** buffer,
                                 int* errnop) {
  size_t bytes_to_write = value.length() + 1;
  if (!CheckSpaceAvailable(bytes_to_write)) {
    *errnop = ERANGE;
    return false;
  }
  *buffer = static_cast<char*>(Reserve(bytes_to_write));
  strncpy(*buffer, value.c_str(), bytes_to_write);
  return true;
}

bool BufferManager::CheckSpaceAvailable(size_t bytes_to_write) const {
  if (bytes_to_write > buflen_) {
    return false;
  }
  return true;
}

void* BufferManager::Reserve(size_t bytes) {
  if (buflen_ < bytes) {
    std::cerr << "Attempted to reserve more bytes than the buffer can hold!"
              << "\n";
    abort();
  }
  void* result = buf_;
  buf_ += bytes;
  buflen_ -= bytes;
  return result;
}

NssCache::NssCache(int cache_size)
    : cache_size_(cache_size),
      passwd_cache_(cache_size),
      page_token_(""),
      on_last_page_(false) {}

void NssCache::Reset() {
  page_token_ = "";
  index_ = 0;
  passwd_cache_.clear();
  on_last_page_ = false;
}

bool NssCache::HasNextPasswd() {
  return index_ < passwd_cache_.size() && !passwd_cache_[index_].empty();
}

bool NssCache::GetNextPasswd(BufferManager* buf, passwd* result, int* errnop) {
  if (!HasNextPasswd()) {
    *errnop = ENOENT;
    return false;
  }
  string cached_passwd = passwd_cache_[index_];
  bool success = ParseJsonToPasswd(cached_passwd, result, buf, errnop);
  if (success) {
    index_++;
  }
  return success;
}

bool NssCache::LoadJsonArrayToCache(string response) {
  Reset();
  json_object* root = NULL;
  root = json_tokener_parse(response.c_str());
  if (root == NULL) {
    return false;
  }
  // First grab the page token.
  json_object* page_token_object;
  if (json_object_object_get_ex(root, "nextPageToken", &page_token_object)) {
    page_token_ = json_object_get_string(page_token_object);
  } else {
    // If the page token is not found, assume something went wrong.
    page_token_ = "";
    on_last_page_ = true;
    return false;
  }
  // A page_token of 0 means we are done. This response will not contain any
  // login profiles.
  if (page_token_ == "0") {
    page_token_ = "";
    on_last_page_ = true;
    return false;
  }
  // Now grab all of the loginProfiles.
  json_object* login_profiles = NULL;
  if (!json_object_object_get_ex(root, "loginProfiles", &login_profiles)) {
    page_token_ = "";
    return false;
  }
  if (json_object_get_type(login_profiles) != json_type_array) {
    return false;
  }
  int arraylen = json_object_array_length(login_profiles);
  if (arraylen == 0 || arraylen > cache_size_) {
    page_token_ = "";
    return false;
  }
  for (int i = 0; i < arraylen; i++) {
    json_object* profile = json_object_array_get_idx(login_profiles, i);
    passwd_cache_.push_back(
        json_object_to_json_string_ext(profile, JSON_C_TO_STRING_PLAIN));
  }
  return true;
}

bool NssCache::NssGetpwentHelper(BufferManager* buf, struct passwd* result,
                                 int* errnop) {
  if (!HasNextPasswd() && !OnLastPage()) {
    std::stringstream url;
    url << kMetadataServerUrl << "users?pagesize=" << cache_size_;
    string page_token = GetPageToken();
    if (!page_token.empty()) {
      url << "&pagetoken=" << page_token;
    }
    string response;
    long http_code = 0;
    if (!HttpGet(url.str(), &response, &http_code) || http_code != 200 ||
        response.empty() || !LoadJsonArrayToCache(response)) {
      // It is possible this to be true after LoadJsonArrayToCache(), so we
      // must check it again.
      if(!OnLastPage()) {
        *errnop = ENOENT;
      }
      return false;
    }
  }
  if (HasNextPasswd() && !GetNextPasswd(buf, result, errnop)) {
    return false;
  }
  return true;
}

size_t OnCurlWrite(void* buf, size_t size, size_t nmemb, void* userp) {
  if (userp) {
    std::ostream& os = *static_cast<std::ostream*>(userp);
    std::streamsize len = size * nmemb;
    if (os.write(static_cast<char*>(buf), len)) {
      return len;
    }
  }
  return 0;
}

bool HttpDo(const string& url, const string& data, string* response,
            long* http_code) {
  if (response == NULL || http_code == NULL) {
    return false;
  }
  CURLcode code(CURLE_FAILED_INIT);
  curl_global_init(CURL_GLOBAL_ALL & ~CURL_GLOBAL_SSL);
  CURL* curl = curl_easy_init();
  std::ostringstream response_stream;
  int retry_count = 0;
  if (curl) {
    struct curl_slist* header_list = NULL;
    header_list = curl_slist_append(header_list, "Metadata-Flavor: Google");
    if (header_list == NULL) {
      curl_easy_cleanup(curl);
      curl_global_cleanup();
      return false;
    }
    do {
      response_stream.str("");
      response_stream.clear();
      curl_easy_setopt(curl, CURLOPT_HTTPHEADER, header_list);
      curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, &OnCurlWrite);
      curl_easy_setopt(curl, CURLOPT_FILE, &response_stream);
      curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5);
      curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
      if (data != "") {
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());
      }

      code = curl_easy_perform(curl);
      if (code != CURLE_OK) {
        curl_easy_cleanup(curl);
        curl_global_cleanup();
        return false;
      }
      curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, http_code);
    } while (retry_count++ < kMaxRetries && *http_code == 500);
    curl_slist_free_all(header_list);
  }
  *response = response_stream.str();
  curl_easy_cleanup(curl);
  curl_global_cleanup();
  return true;
}

bool HttpGet(const string& url, string* response, long* http_code) {
  return HttpDo(url, "", response, http_code);
}

bool HttpPost(const string& url, const string& data, string* response,
              long* http_code) {
  return HttpDo(url, data, response, http_code);
}

bool ValidateUserName(const string& user_name) {
  Regex::regex r(kUserNameRegex);
  return Regex::regex_match(user_name, r);
}

string UrlEncode(const string& param) {
  CURL* curl = curl_easy_init();
  char* encoded = curl_easy_escape(curl, param.c_str(), param.length());
  if (encoded == NULL) {
    curl_easy_cleanup(curl);
    return "";
  }
  string encoded_param = encoded;
  curl_free(encoded);
  curl_easy_cleanup(curl);
  return encoded_param;
}

bool ValidatePasswd(struct passwd* result, BufferManager* buf,
                    int* errnop) {
  // OS Login disallows uids less than 1000.
  if (result->pw_uid < 1000) {
    *errnop = EINVAL;
    return false;
  }
  if (result->pw_gid == 0) {
    *errnop = EINVAL;
    return false;
  }
  if (strlen(result->pw_name) == 0) {
    *errnop = EINVAL;
    return false;
  }
  if (strlen(result->pw_dir) == 0) {
    string home_dir = "/home/";
    home_dir.append(result->pw_name);
    if (!buf->AppendString(home_dir, &result->pw_dir, errnop)) {
      return false;
    }
  }
  if (strlen(result->pw_shell) == 0) {
    if (!buf->AppendString(DEFAULT_SHELL, &result->pw_shell, errnop)) {
      return false;
    }
  }

  // OS Login does not utilize the passwd field and reserves the gecos field.
  // Set these to be empty.
  if (!buf->AppendString("", &result->pw_gecos, errnop)) {
    return false;
  }
  if (!buf->AppendString("", &result->pw_passwd, errnop)) {
    return false;
  }
  return true;
}

std::vector<string> ParseJsonToSshKeys(const string& json) {
  std::vector<string> result;
  json_object* root = NULL;
  root = json_tokener_parse(json.c_str());
  if (root == NULL) {
    return result;
  }
  // Locate the sshPublicKeys object.
  json_object* login_profiles = NULL;
  if (!json_object_object_get_ex(root, "loginProfiles", &login_profiles)) {
    return result;
  }
  if (json_object_get_type(login_profiles) != json_type_array) {
    return result;
  }
  login_profiles = json_object_array_get_idx(login_profiles, 0);

  json_object* ssh_public_keys = NULL;
  if (!json_object_object_get_ex(login_profiles, "sshPublicKeys",
                                 &ssh_public_keys)) {
    return result;
  }

  if (json_object_get_type(ssh_public_keys) != json_type_object) {
    return result;
  }
  json_object_object_foreach(ssh_public_keys, key, val) {
    json_object* iter;
    if (!json_object_object_get_ex(ssh_public_keys, key, &iter)) {
      return result;
    }
    if (json_object_get_type(iter) != json_type_object) {
      continue;
    }
    string key_to_add = "";
    bool expired = false;
    json_object_object_foreach(iter, key, val) {
      string string_key(key);
      int val_type = json_object_get_type(val);
      if (string_key == "key") {
        if (val_type != json_type_string) {
          continue;
        }
        key_to_add = (char*)json_object_get_string(val);
      }
      if (string_key == "expirationTimeUsec") {
        if (val_type == json_type_int || val_type == json_type_string) {
          uint64_t expiry_usec = (uint64_t)json_object_get_int64(val);
          struct timeval tp;
          gettimeofday(&tp, NULL);
          uint64_t cur_usec = tp.tv_sec * 1000000 + tp.tv_usec;
          expired = cur_usec > expiry_usec;
        } else {
          continue;
        }
      }
    }
    if (!key_to_add.empty() && !expired) {
      result.push_back(key_to_add);
    }
  }
  return result;
}

bool ParseJsonToPasswd(const string& json, struct passwd* result,
                       BufferManager* buf, int* errnop) {
  json_object* root = NULL;
  root = json_tokener_parse(json.c_str());
  if (root == NULL) {
    *errnop = ENOENT;
    return false;
  }
  json_object* login_profiles = NULL;
  // If this is called from getpwent_r, loginProfiles won't be in the response.
  if (json_object_object_get_ex(root, "loginProfiles", &login_profiles)) {
    if (json_object_get_type(login_profiles) != json_type_array) {
      return false;
    }
    root = login_profiles;
    root = json_object_array_get_idx(root, 0);
  }
  // Locate the posixAccounts object.
  json_object* posix_accounts = NULL;
  if (!json_object_object_get_ex(root, "posixAccounts", &posix_accounts)) {
    *errnop = ENOENT;
    return false;
  }
  if (json_object_get_type(posix_accounts) != json_type_array) {
    return false;
  }
  posix_accounts = json_object_array_get_idx(posix_accounts, 0);

  // Populate with some default values that ValidatePasswd can detect if they
  // are not set.
  result->pw_uid = 0;
  result->pw_shell = (char*)"";
  result->pw_name = (char*)"";
  result->pw_dir = (char*)"";

  // Iterate through the json response and populate the passwd struct.
  if (json_object_get_type(posix_accounts) != json_type_object) {
    return false;
  }
  json_object_object_foreach(posix_accounts, key, val) {
    int val_type = json_object_get_type(val);
    // Convert char* to c++ string for easier comparison.
    string string_key(key);

    if (string_key == "uid") {
      if (val_type == json_type_int || val_type == json_type_string) {
        result->pw_uid = (uint32_t)json_object_get_int64(val);
        if (result->pw_uid == 0) {
          *errnop = EINVAL;
          return false;
        }
      } else {
        *errnop = EINVAL;
        return false;
      }
    } else if (string_key == "gid") {
      if (val_type == json_type_int || val_type == json_type_string) {
        result->pw_gid = (uint32_t)json_object_get_int64(val);
        // Use the uid as the default group when gid is not set or is zero.
        if (result->pw_gid == 0) {
          result->pw_gid = result->pw_uid;
        }
      } else {
        *errnop = EINVAL;
        return false;
      }
    } else if (string_key == "username") {
      if (val_type != json_type_string) {
        *errnop = EINVAL;
        return false;
      }
      if (!buf->AppendString((char*)json_object_get_string(val),
                             &result->pw_name, errnop)) {
        return false;
      }
    } else if (string_key == "homeDirectory") {
      if (val_type != json_type_string) {
        *errnop = EINVAL;
        return false;
      }
      if (!buf->AppendString((char*)json_object_get_string(val),
                             &result->pw_dir, errnop)) {
        return false;
      }
    } else if (string_key == "shell") {
      if (val_type != json_type_string) {
        *errnop = EINVAL;
        return false;
      }
      if (!buf->AppendString((char*)json_object_get_string(val),
                             &result->pw_shell, errnop)) {
        return false;
      }
    }
  }

  return ValidatePasswd(result, buf, errnop);
}

bool ParseJsonToEmail(const string& json, string* email) {
  json_object* root = NULL;
  root = json_tokener_parse(json.c_str());
  if (root == NULL) {
    return false;
  }
  // Locate the email object.
  json_object* login_profiles = NULL;
  if (!json_object_object_get_ex(root, "loginProfiles", &login_profiles)) {
    return false;
  }
  if (json_object_get_type(login_profiles) != json_type_array) {
    return false;
  }
  login_profiles = json_object_array_get_idx(login_profiles, 0);
  json_object* json_email = NULL;
  if (!json_object_object_get_ex(login_profiles, "name", &json_email)) {
    return false;
  }

  *email = json_object_get_string(json_email);
  return true;
}

bool ParseJsonToSuccess(const string& json) {
  json_object* root = NULL;
  root = json_tokener_parse(json.c_str());
  if (root == NULL) {
    return false;
  }
  json_object* success = NULL;
  if (!json_object_object_get_ex(root, "success", &success)) {
    return false;
  }
  return (bool)json_object_get_boolean(success);
}

bool ParseJsonToKey(const string& json, const string& key, string* response) {
  json_object* root = NULL;
  json_object* json_response = NULL;
  const char* c_response;

  root = json_tokener_parse(json.c_str());
  if (root==NULL) {
    return false;
  }

  if (!json_object_object_get_ex(root, key.c_str(), &json_response)) {
    return false;
  }

  if (!(c_response = json_object_get_string(json_response))) {
    return false;
  }

  *response = c_response;
  return true;
}

bool ParseJsonToChallenges(const string& json,
                           std::vector<Challenge> *challenges) {
  json_object* root = NULL;

  root = json_tokener_parse(json.c_str());
  if (root == NULL) {
    return false;
  }

  json_object *jsonChallenges = NULL;
  if (!json_object_object_get_ex(root, "challenges", &jsonChallenges)) {
    return false;
  }

  json_object *challengeId, *challengeType, *challengeStatus = NULL;
  for (int i = 0; i < json_object_array_length(jsonChallenges); ++i) {
    if (!json_object_object_get_ex(json_object_array_get_idx(jsonChallenges, i),
                                   "challengeId", &challengeId)) {
      return false;
    }
    if (!json_object_object_get_ex(json_object_array_get_idx(jsonChallenges, i),
                                   "challengeType", &challengeType)) {
      return false;
    }
    if (!json_object_object_get_ex(json_object_array_get_idx(jsonChallenges, i),
                                   "status", &challengeStatus)) {
      return false;
    }
    Challenge challenge;
    challenge.id = json_object_get_int(challengeId);
    challenge.type = json_object_get_string(challengeType);
    challenge.status = json_object_get_string(challengeStatus);

    challenges->push_back(challenge);
  }

  return true;
}

bool GetUser(const string& username, string* response) {
  std::stringstream url;
  url << kMetadataServerUrl << "users?username=" << UrlEncode(username);

  long http_code = 0;
  if (!HttpGet(url.str(), response, &http_code) || response->empty()
      || http_code != 200) {
    return false;
  }
  return true;
}

bool StartSession(const string& email, string* response) {
  bool ret = true;
  struct json_object *jobj, *jarr;

  jarr = json_object_new_array();
  json_object_array_add(jarr, json_object_new_string(INTERNAL_TWO_FACTOR));
  json_object_array_add(jarr, json_object_new_string(TOTP));
  json_object_array_add(jarr, json_object_new_string(IDV_PREREGISTERED_PHONE));

  jobj = json_object_new_object();
  json_object_object_add(jobj, "email", json_object_new_string(email.c_str()));
  json_object_object_add(jobj, "supportedChallengeTypes", jarr);

  const char* data;
  data = json_object_to_json_string_ext(jobj, JSON_C_TO_STRING_PLAIN);

  std::stringstream url;
  url << kMetadataServerUrl << "authenticate/sessions/start";

  long http_code = 0;
  if (!HttpPost(url.str(), data, response, &http_code) || response->empty()
      || http_code != 200) {
    ret = false;
  }

  json_object_put(jarr);
  json_object_put(jobj);

  return ret;
}

bool ContinueSession(const string& email, const string& user_token,
                     const string& session_id, const Challenge& challenge,
                     string* response) {
  bool ret = true;
  struct json_object *jobj, *jresp;

  jobj = json_object_new_object();
  json_object_object_add(jobj, "email", json_object_new_string(email.c_str()));
  json_object_object_add(jobj, "challengeId",
                         json_object_new_int(challenge.id));

  if (challenge.type != AUTHZEN) {
    jresp = json_object_new_object();
    json_object_object_add(jresp, "credential",
                           json_object_new_string(user_token.c_str()));
    json_object_object_add(jobj, "proposalResponse", jresp);
  }

  if (challenge.status != "READY") {
    json_object_object_add(jobj, "action",
                           json_object_new_string("startAlternate"));
  }

  const char* data = NULL;
  data = json_object_to_json_string_ext(jobj, JSON_C_TO_STRING_PLAIN);

  std::stringstream url;
  url << kMetadataServerUrl << "authenticate/sessions/"
      << session_id << "/continue";
  long http_code = 0;
  if (!HttpPost(url.str(), data, response, &http_code) || response->empty()
      || http_code != 200) {
    ret = false;
  }

  json_object_put(jobj);
  if (challenge.type != AUTHZEN) {
    json_object_put(jresp);
  }

  return ret;
}
}  // namespace oslogin_utils
