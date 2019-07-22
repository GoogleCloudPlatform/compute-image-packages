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
using oslogin_utils::ParseJsonToPasswd;
using oslogin_utils::UrlEncode;

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
  // If there is no cache file, we will assume there are no groups.
  if (access(OSLOGIN_GROUP_CACHE_PATH, R_OK) != 0)
    return NSS_STATUS_NOTFOUND;
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

// look for OS Login user with uid matching the requested gid, and craft a
// self-group for it.
enum nss_status getselfgrgid(gid_t gid, struct group *grp,
                                          char *buf, size_t buflen) {
  BufferManager buffer_manager(buf, buflen);
  std::stringstream url;
  url << kMetadataServerUrl << "users?uid=" << gid;
  string response;
  long http_code = 0;
  if (!HttpGet(url.str(), &response, &http_code) || http_code != 200 ||
      response.empty()) {
    return NSS_STATUS_NOTFOUND;
  }
  struct passwd result;
  int errnop;
  if (!ParseJsonToPasswd(response, &result, &buffer_manager, &errnop))
    return NSS_STATUS_NOTFOUND;

  if (result.pw_gid != result.pw_uid)
    return NSS_STATUS_NOTFOUND;

  // Set the group name to the name of the matching user.
  if (!buffer_manager.AppendString(result.pw_name, &grp->gr_name, &errnop))
    return NSS_STATUS_NOTFOUND;

  grp->gr_gid = result.pw_uid;

  // Create a list of only the matching user and add to members list.
  std::vector<string> members;
  members.push_back(string(result.pw_name));
  if (!AddUsersToGroup(members, grp, &buffer_manager, &errnop))
    return NSS_STATUS_NOTFOUND;

  return NSS_STATUS_SUCCESS;
}

// look for OS Login user with name matching the requested name, and craft a
// self-group for it.
enum nss_status getselfgrnam(const char* name, struct group *grp,
                                          char *buf, size_t buflen) {
  BufferManager buffer_manager(buf, buflen);
  std::stringstream url;
  url << kMetadataServerUrl << "users?username=" << UrlEncode(string(name));
  string response;
  long http_code = 0;
  if (!HttpGet(url.str(), &response, &http_code) || http_code != 200 ||
      response.empty()) {
    return NSS_STATUS_NOTFOUND;
  }
  struct passwd result;
  int errnop;
  if (!ParseJsonToPasswd(response, &result, &buffer_manager, &errnop))
    return NSS_STATUS_NOTFOUND;

  if (result.pw_gid != result.pw_uid)
    return NSS_STATUS_NOTFOUND;

  // Set the group name to the name of the matching user.
  if (!buffer_manager.AppendString(result.pw_name, &grp->gr_name, &errnop))
    return NSS_STATUS_NOTFOUND;

  grp->gr_gid = result.pw_uid;

  // Create a list of only the matching user and add to members list.
  std::vector<string> members;
  members.push_back(string(result.pw_name));
  if (!AddUsersToGroup(members, grp, &buffer_manager, &errnop))
    return NSS_STATUS_NOTFOUND;

  return NSS_STATUS_SUCCESS;
}

// _nss_olosing_getgrgid_r()
// Get a group entry by id.

enum nss_status _nss_oslogin_getgrgid_r(gid_t gid, struct group *grp, char *buf,
                                        size_t buflen, int *errnop) {
  memset(grp, 0, sizeof(struct group));
  if (getselfgrgid(gid, grp, buf, buflen) == NSS_STATUS_SUCCESS)
      return NSS_STATUS_SUCCESS;
  grp->gr_gid = gid;
  return _nss_oslogin_getgrby(grp, buf, buflen, errnop);
}

// _nss_oslogin_getgrnam_r()
// Get a group entry by name.

enum nss_status _nss_oslogin_getgrnam_r(const char *name, struct group *grp,
                                        char *buf, size_t buflen, int *errnop) {
  memset(grp, 0, sizeof(struct group));
  if (getselfgrnam(name, grp, buf, buflen) == NSS_STATUS_SUCCESS)
      return NSS_STATUS_SUCCESS;
  grp->gr_name = (char *)name;
  return _nss_oslogin_getgrby(grp, buf, buflen, errnop);
}

// _nss_cache_oslogin_initgroups_dyn()
// Initialize groups for new session.

enum nss_status _nss_oslogin_initgroups_dyn(const char *user, gid_t skipgroup,
                                            long int *start, long int *size,
                                            gid_t **groupsp, long int limit,
                                            int *errnop) {
  // check if user exists in local passwd DB
  FILE *p_file = fopen(PASSWD_PATH, "r");
  if (p_file == NULL)
    return NSS_STATUS_NOTFOUND;
  struct passwd *userp;
  while ((userp = fgetpwent(p_file)) != NULL)
    if (strcmp(userp->pw_name, user) == 0)
      return NSS_STATUS_NOTFOUND;
  fclose(p_file);

  std::vector<Group> grouplist;
  if (!GetGroupsForUser(string(user), &grouplist, errnop)) {
      return NSS_STATUS_NOTFOUND;
  }

  gid_t *groups = *groupsp;
  int i;
  for (i = 0; i < (int) grouplist.size(); i++) {
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

  return NSS_STATUS_SUCCESS;
}

// nss_getpwent_r() is intentionally left unimplemented. This functionality is
// now covered by the nss_cache binary and nss_cache module.

nss_status _nss_oslogin_getpwent_r() { return NSS_STATUS_NOTFOUND; }
nss_status _nss_oslogin_endpwent() { return NSS_STATUS_SUCCESS; }
nss_status _nss_oslogin_setpwent() { return NSS_STATUS_SUCCESS; }

nss_status _nss_oslogin_getgrent_r() { return NSS_STATUS_NOTFOUND; }
nss_status _nss_oslogin_endgrent() { return NSS_STATUS_SUCCESS; }
nss_status _nss_oslogin_setgrent() { return NSS_STATUS_SUCCESS; }

NSS_METHOD_PROTOTYPE(__nss_compat_getpwnam_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getpwuid_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getpwent_r);
NSS_METHOD_PROTOTYPE(__nss_compat_setpwent);
NSS_METHOD_PROTOTYPE(__nss_compat_endpwent);

NSS_METHOD_PROTOTYPE(__nss_compat_getgrnam_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getgrgid_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getgrent_r);
NSS_METHOD_PROTOTYPE(__nss_compat_setgrent);
NSS_METHOD_PROTOTYPE(__nss_compat_endgrent);

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
