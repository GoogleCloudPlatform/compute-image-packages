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

#include <curl/curl.h>
#include <errno.h>
#include <grp.h>
#include <nss.h>
#include <pthread.h>
#include <pwd.h>
#include <sys/types.h>
#include <syslog.h>
#include <unistd.h>

#include <iostream>
#include <sstream>
#include <string>

#include "../utils/oslogin_utils.h"

using std::string;

using oslogin_utils::BufferManager;
using oslogin_utils::HttpGet;
using oslogin_utils::MutexLock;
using oslogin_utils::NssCache;
using oslogin_utils::ParseJsonToPasswd;
using oslogin_utils::UrlEncode;

// Metadata server URL.
static const char kMetadataServerUrl[] =
   "http://metadata.google.internal/computeMetadata/v1/oslogin/";

// Size of the NssCache. This also determines how many users will be requested
// per HTTP call.
static const uint64_t kNssCacheSize = 2048;

// NssCache for storing passwd entries.
static NssCache nss_cache(kNssCacheSize);

// Protects access to nss_cache.
static pthread_mutex_t cache_mutex = PTHREAD_MUTEX_INITIALIZER;

extern "C" {

// Get a passwd entry by id.
int _nss_oslogin_getpwuid_r(uid_t uid, struct passwd *result, char *buffer,
                            size_t buflen, int *errnop) {
  BufferManager buffer_manager(buffer, buflen);
  std::stringstream url;
  url << kMetadataServerUrl << "users?uid=" << uid;
  string response = HttpGet(url.str());
  if (response.empty()) {
    *errnop = ENOENT;
    return NSS_STATUS_NOTFOUND;
  }
  if (!ParseJsonToPasswd(response, result, &buffer_manager, errnop)) {
    if(*errnop == EINVAL) {
      openlog("nss_oslogin", LOG_PID, LOG_USER);
      syslog(LOG_ERR, "Received malformed response from server: %s",
             response.c_str());
      closelog();
    }
    return *errnop == ERANGE ? NSS_STATUS_TRYAGAIN : NSS_STATUS_NOTFOUND;
  }
  return NSS_STATUS_SUCCESS;
}

// Get a passwd entry by name.
int _nss_oslogin_getpwnam_r(const char *name, struct passwd *result,
                            char *buffer, size_t buflen, int *errnop) {
  BufferManager buffer_manager(buffer, buflen);
  std::stringstream url;
  url << kMetadataServerUrl << "users?username=" << UrlEncode(name);
  string response = HttpGet(url.str());
  if (response.empty()) {
    *errnop = ENOENT;
    return NSS_STATUS_NOTFOUND;
  }
  if (!ParseJsonToPasswd(response, result, &buffer_manager, errnop)) {
    if (*errnop == EINVAL) {
      openlog("nss_oslogin", LOG_PID, LOG_USER);
      syslog(LOG_ERR, "Received malformed response from server: %s",
             response.c_str());
      closelog();
    }
    return *errnop == ERANGE ? NSS_STATUS_TRYAGAIN : NSS_STATUS_NOTFOUND;
  }
  return NSS_STATUS_SUCCESS;
}

// Open the passwd database.
int _nss_oslogin_setpwent(void) {
  // All this method does is reset to the beginning of the database.
  MutexLock ml(&cache_mutex);
  nss_cache.Reset();
  return NSS_STATUS_SUCCESS;
}

// Close the passwd database.
int _nss_oslogin_endpwent(void) {
  // Here we should probably just reset the nss_cache too.
  MutexLock ml(&cache_mutex);
  nss_cache.Reset();
  return NSS_STATUS_SUCCESS;
}

// Grab the next entry from the passwd database.
int _nss_oslogin_getpwent_r(struct passwd *result, char *buffer, size_t buflen,
                           int *errnop) {
  BufferManager buffer_manager(buffer, buflen);
  MutexLock ml(&cache_mutex);
  if (!nss_cache.HasNextPasswd() && !nss_cache.OnLastPage()) {
    std::stringstream url;
    url << kMetadataServerUrl << "users?pagesize=" << kNssCacheSize;
    string page_token = nss_cache.GetPageToken();
    if (!page_token.empty()) {
      url << "&pagetoken=" << page_token;
    }
    string response = HttpGet(url.str());
    if (response.empty()) {
      *errnop = ENOENT;
      return NSS_STATUS_NOTFOUND;
    }
    if (!nss_cache.LoadJsonArrayToCache(response)) {
      *errnop = ENOENT;
      return NSS_STATUS_NOTFOUND;
    }
  }
  if (!nss_cache.GetNextPasswd(&buffer_manager, result, errnop)) {
    if (*errnop == EINVAL) {
      openlog("nss_oslogin", LOG_PID, LOG_USER);
      syslog(LOG_ERR, "Encountered malformed passwd entry in cache.");
      closelog();
    }
    return *errnop == ERANGE ? NSS_STATUS_TRYAGAIN : NSS_STATUS_NOTFOUND;
  }
  return NSS_STATUS_SUCCESS;
}
}  // extern "C"
