// Copyright 2018 Google Inc. All Rights Reserved.
//
//
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

#include <errno.h>
#include <nss.h>
#include <pthread.h>
#include <pwd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <syslog.h>
#include <unistd.h>
#include <sstream>


#include <fstream>

#include <compat.h>
#include <oslogin_utils.h>

using oslogin_utils::BufferManager;
using oslogin_utils::MutexLock;
using oslogin_utils::NssCache;
using oslogin_utils::GetUsersForGroup;

// File paths for the nss cache file.
static const char kDefaultFilePath[] = K_DEFAULT_PFILE_PATH;
static const char kDefaultBackupFilePath[] = K_DEFAULT_BACKUP_PFILE_PATH;
static const char kDefaultGroupPath[] = K_DEFAULT_GFILE_PATH;
static const char kDefaultBackupGroupPath[] = K_DEFAULT_BACKUP_GFILE_PATH;

// Local NSS Cache size. This affects the maximum number of passwd or group
// entries per http request.
static const uint64_t kNssCacheSize = 499;

// Passwd buffer size. We are guaranteed that a single OS Login user will not
// exceed 32k.
static const uint64_t kPasswdBufferSize = 32768;

static NssCache nss_cache(kNssCacheSize);

int refreshpasswdcache() {
  int error_code = 0;
  // Temporary buffer to hold passwd entries before writing.
  char buffer[kPasswdBufferSize];
  struct passwd pwd;

  std::ofstream cache_file(kDefaultBackupFilePath);
  if (cache_file.fail()) {
    openlog("oslogin_cache_refresh", LOG_PID, LOG_USER);
    syslog(LOG_ERR, "Failed to open file %s.", kDefaultFilePath);
    closelog();
    return -1;
  }
  chown(kDefaultFilePath, 0, 0);
  chmod(kDefaultFilePath, S_IRUSR | S_IWUSR | S_IROTH);

  int count = 0;
  nss_cache.Reset();
  while (!nss_cache.OnLastPage() || nss_cache.HasNextEntry()) {
    BufferManager buffer_manager(buffer, kPasswdBufferSize);
    if (!nss_cache.NssGetpwentHelper(&buffer_manager, &pwd, &error_code)) {
      break;
    }
    cache_file << pwd.pw_name << ":" << pwd.pw_passwd << ":" << pwd.pw_uid << ":" << pwd.pw_gid << ":" << pwd.pw_gecos << ":" << pwd.pw_dir << ":" << pwd.pw_shell << "\n";
    count++;
  }
  cache_file.close();

  // Check for errors.
  if (error_code) {
    openlog("oslogin_cache_refresh", LOG_PID, LOG_USER);
    if (error_code == ERANGE) {
      syslog(LOG_ERR, "Received unusually large passwd entry.");
    } else if (error_code == EINVAL) {
      syslog(LOG_ERR, "Encountered malformed passwd entry.");
    } else {
      syslog(LOG_ERR, "Unknown error while retrieving passwd entry.");
    }
    closelog();
    remove(kDefaultBackupFilePath);
    return error_code;
  }

  if ((count > 0) && (rename(kDefaultBackupFilePath, kDefaultFilePath) != 0)) {
    openlog("oslogin_cache_refresh", LOG_PID, LOG_USER);
    syslog(LOG_ERR, "Could not move passwd cache file.");
    closelog();
    remove(kDefaultBackupFilePath);
  }

  return error_code;
}

int refreshgroupcache() {
  int error_code = 0;
  // Temporary buffer to hold passwd entries before writing.
  char buffer[kPasswdBufferSize];

  std::ofstream cache_file(kDefaultBackupGroupPath);
  if (cache_file.fail()) {
    openlog("oslogin_cache_refresh", LOG_PID, LOG_USER);
    syslog(LOG_ERR, "Failed to open file %s.", kDefaultBackupGroupPath);
    closelog();
    return -1;
  }
  chown(kDefaultGroupPath, 0, 0);
  chmod(kDefaultGroupPath, S_IRUSR | S_IWUSR | S_IROTH);

  struct group grp;
  int count = 0;
  nss_cache.Reset();
  while (!nss_cache.OnLastPage() || nss_cache.HasNextEntry()) {
    BufferManager buffer_manager(buffer, kPasswdBufferSize);
    if (!nss_cache.NssGetgrentHelper(&buffer_manager, &grp, &error_code)) {
      break;
    }
    // TODO: instantiate these vars once or each time ?
    std::vector<string> users;
    std::string name(grp.gr_name);
    if (!GetUsersForGroup(name, &users, &error_code)) {
      break;
    }
    cache_file << grp.gr_name << ":" << grp.gr_passwd << ":" << grp.gr_gid << ":" << users.front();
    users.erase(users.begin());
    for (auto &user : users) {
      cache_file << "," << user;
    }
    cache_file << "\n";
    count++;
  }
  cache_file.close();

  // Check for errors.
  if (error_code) {
    openlog("oslogin_cache_refresh", LOG_PID, LOG_USER);
    if (error_code == ERANGE) {
      syslog(LOG_ERR, "Received unusually large group entry.");
    } else if (error_code == EINVAL) {
      syslog(LOG_ERR, "Encountered malformed group entry.");
    } else {
      syslog(LOG_ERR, "Unknown error while retrieving group entry.");
    }
    closelog();
    remove(kDefaultBackupGroupPath);
    return error_code;
  }

  if ((count > 0) && (rename(kDefaultBackupGroupPath, kDefaultGroupPath) != 0)) {
    openlog("oslogin_cache_refresh", LOG_PID, LOG_USER);
    syslog(LOG_ERR, "Could not move group cache file.");
    closelog();
    remove(kDefaultBackupGroupPath);
  }

  return error_code;
}

int main() {
  int u_res, g_res;
  u_res = refreshpasswdcache();
  g_res = refreshgroupcache();
  if (u_res != 0)
    return u_res;
  return g_res;
}
