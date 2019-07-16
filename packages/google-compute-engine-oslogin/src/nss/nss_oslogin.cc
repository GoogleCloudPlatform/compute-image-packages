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

#include <compat.h>
#include <oslogin_utils.h>

#include <curl/curl.h>
#include <errno.h>
#include <grp.h>
#include <nss.h>
#include <pwd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/param.h>
#include <syslog.h>
#include <unistd.h>
#include <stdlib.h>

#include <iostream>
#include <sstream>
#include <string>

using std::string;

using oslogin_utils::AddUsersToGroup;
using oslogin_utils::BufferManager;
using oslogin_utils::FindGroup;
using oslogin_utils::GetGroupsForUser;
using oslogin_utils::GetUsersForGroup;
using oslogin_utils::Group;
using oslogin_utils::HttpGet;
using oslogin_utils::kMetadataServerUrl;
using oslogin_utils::NssCache;
using oslogin_utils::ParseJsonToPasswd;
using oslogin_utils::UrlEncode;

// Size of the NssCache. This also determines how many users will be requested
// per HTTP call.
static const uint64_t kNssCacheSize = 2048;

// NssCache for storing passwd entries.
static NssCache nss_cache(kNssCacheSize);

extern "C" {

// Get a passwd entry by id.
enum nss_status _nss_oslogin_getpwuid_r(uid_t uid, struct passwd *result,
                                        char *buffer, size_t buflen,
                                        int *errnop) {
  BufferManager buffer_manager(buffer, buflen);
  std::stringstream url;
  url << kMetadataServerUrl << "users?uid=" << uid;
  string response;
  long http_code = 0;
  if (!HttpGet(url.str(), &response, &http_code) || http_code != 200 ||
      response.empty()) {
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

// Get a passwd entry by name.
enum nss_status _nss_oslogin_getpwnam_r(const char *name, struct passwd *result,
                                        char *buffer, size_t buflen,
                                        int *errnop) {
  BufferManager buffer_manager(buffer, buflen);
  std::stringstream url;
  url << kMetadataServerUrl << "users?username=" << UrlEncode(name);
  string response;
  long http_code = 0;
  if (!HttpGet(url.str(), &response, &http_code) || http_code != 200 ||
      response.empty()) {
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

enum nss_status _nss_oslogin_getgrby(struct group *grp, char *buf,
                                     size_t buflen, int *errnop) {
  BufferManager buffer_manager(buf, buflen);
  if (!FindGroup(grp, &buffer_manager, errnop))
    return *errnop == ERANGE ? NSS_STATUS_TRYAGAIN : NSS_STATUS_NOTFOUND;

  std::vector<string> users;
  if (!GetUsersForGroup(grp->gr_name, &users, errnop))
    return *errnop == ERANGE ? NSS_STATUS_TRYAGAIN : NSS_STATUS_NOTFOUND;

  if (!AddUsersToGroup(users, grp, &buffer_manager, errnop))
    return *errnop == ERANGE ? NSS_STATUS_TRYAGAIN : NSS_STATUS_NOTFOUND;

  return NSS_STATUS_SUCCESS;
}

// Get a group entry by id.
enum nss_status _nss_oslogin_getgrgid_r(gid_t gid, struct group *grp, char *buf,
                                        size_t buflen, int *errnop) {
  grp->gr_gid = gid;
  return _nss_oslogin_getgrby(grp, buf, buflen, errnop);
}

// Get a group entry by name.
enum nss_status _nss_oslogin_getgrnam_r(const char *name, struct group *grp,
                                        char *buf, size_t buflen, int *errnop) {
  grp->gr_name = (char *)name;
  return _nss_oslogin_getgrby(grp, buf, buflen, errnop);
}

bool initgroups_cached(const char *user, struct group *cached, char *buffer,
                       size_t buflen, struct group **cachedp) {
  static FILE *g_file = NULL;
  if (!(g_file = fopen(OSLOGIN_INITGROUP_CACHE_PATH, "r"))) {
    return false;
  }
  while (fgetgrent_r(g_file, cached, buffer, buflen, cachedp) == 0) {
      if (!strcmp(cached->gr_name, user)) break;
  }
  return (cachedp != NULL) && 
      (cached->gr_gid >= (time(NULL) - INITGROUP_CACHE_EXPIRE_SECONDS));
}

bool update_initcache(struct group *updated) {
  static FILE *g_file = NULL;
  if (!(g_file = fopen(OSLOGIN_INITGROUP_CACHE_PATH, "rw"))) {
    return false;
  }

  struct group result;
  struct group *resultp;
  size_t buflen = 255;
  char buffer[buflen];
  while (fgetgrent_r(g_file, &result, buffer, buflen, &resultp) == 0) {
    if (!strcmp(result.gr_name, updated->gr_name)) {
      DEBUG("Found entry to delete\n");
      // WHAT is the writing strategy?
      // once we find our matching line, begin saving all lines after that, then
      // rewind to the match pos and write all the saved-in-memory lines. the
      // amount stored in memory can be at most the whole file. if we append
      // newest entries, files are more likely to be stale the higher up in the
      // file they are. better to put new entries on top, but this really does
      // mean rewriting the whole file each time. instead, maybe append, but
      // read the file in reverse order for purposes of finding lines? reading
      // files backwards is hard. it seems very likely that we'll be reading the
      // whole file into memory quite often.
    }
  }
  return true;
}

// _nss_cache_oslogin_initgroups_dyn()
// Initialize groups for new session.

enum nss_status _nss_oslogin_initgroups_dyn(const char *user, gid_t skipgroup,
                                            long int *start, long int *size,
                                            gid_t **groupsp, long int limit,
                                            int *errnop) {
  std::vector<Group> grouplist;
  DEBUG("Initrgroups for %s\n", user);

  struct group cached;
  struct group *cachedp;
  size_t buflen = 255;
  char buffer[buflen];
  bool found;
  DEBUG("Checking cache\n");
  if ((found = initgroups_cached(user, &cached, buffer, buflen, &cachedp))) {
    DEBUG("Found user in cache\n");
    for (int idx = 0; cached.gr_mem[idx] != NULL; idx++) {
      Group g;
      g.gid = atoi(cached.gr_mem[idx]);
      grouplist.push_back(g);
    }
  }

  DEBUG("Looking up groups\n");
  if (!found && !GetGroupsForUser(string(user), &grouplist, errnop)) {
      return NSS_STATUS_NOTFOUND;
  }

  gid_t *groups = *groupsp;
  for (int i = 0; i < (int) grouplist.size(); i++) {
    // Resize the buffer if needed.
    if (*start == *size) {
      gid_t *newgroups;
      long int newsize = 2 * *size;
      // Stop at limit if provided.
      if (limit > 0) {
        if (*size >= limit) {
          *errnop = ERANGE;
          return NSS_STATUS_TRYAGAIN;
        }
        newsize = MIN(limit, newsize);
      }
      newgroups = (gid_t *)realloc(groups, newsize * sizeof(gid_t *));
      if (newgroups == NULL) {
        *errnop = EAGAIN;
        return NSS_STATUS_TRYAGAIN;
      }
      *groupsp = groups = newgroups;
      *size = newsize;
    }
    groups[(*start)++] = grouplist[i].gid;
  }

  if (found)
    DEBUG("Would update cache\n");
  //update_initcache(&cached);
  return NSS_STATUS_SUCCESS;
}

// nss_getpwent_r() is intentionally left unimplemented. This functionality is
// now covered by the nss_cache binary and nss_cache module.

nss_status _nss_oslogin_getpwent_r() { return NSS_STATUS_NOTFOUND; }
nss_status _nss_oslogin_endpwent() { return NSS_STATUS_SUCCESS; }
nss_status _nss_oslogin_setpwent() { return NSS_STATUS_SUCCESS; }

NSS_METHOD_PROTOTYPE(__nss_compat_getpwnam_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getpwuid_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getpwent_r);
NSS_METHOD_PROTOTYPE(__nss_compat_setpwent);
NSS_METHOD_PROTOTYPE(__nss_compat_endpwent);
NSS_METHOD_PROTOTYPE(__nss_compat_getgrnam_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getgrgid_r);

DECLARE_NSS_METHOD_TABLE(methods,
                         {NSDB_PASSWD, "getpwnam_r", __nss_compat_getpwnam_r,
                          (void *)_nss_oslogin_getpwnam_r},
                         {NSDB_PASSWD, "getpwuid_r", __nss_compat_getpwuid_r,
                          (void *)_nss_oslogin_getpwuid_r},
                         {NSDB_PASSWD, "getpwent_r", __nss_compat_getpwent_r,
                          (void *)_nss_oslogin_getpwent_r},
                         {NSDB_PASSWD, "endpwent", __nss_compat_endpwent,
                          (void *)_nss_oslogin_endpwent},
                         {NSDB_PASSWD, "setpwent", __nss_compat_setpwent,
                          (void *)_nss_oslogin_setpwent},
                         {NSDB_GROUP, "getgrnam_r", __nss_compat_getgrnam_r,
                          (void *)_nss_oslogin_getgrnam_r},
                         {NSDB_GROUP, "getgrgid_r", __nss_compat_getgrgid_r,
                          (void *)_nss_oslogin_getgrgid_r}, )

NSS_REGISTER_METHODS(methods)
}  // extern "C"
