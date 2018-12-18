// Copyright 2018 Google Inc. All Rights Reserved.
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

#include <fstream>

#include "../compat.h"
#include "../utils/oslogin_utils.h"


using oslogin_utils::BufferManager;
using oslogin_utils::MutexLock;
using oslogin_utils::NssCache;

// File paths for the nss cache file.
static const char kDefaultFilePath[] = K_DEFAULT_FILE_PATH;
static const char kDefaultBackupFilePath[] = K_DEFAULT_BACKUP_FILE_PATH;

// Local NSS Cache size. This affects the maximum number of passwd entries per
// http request.
static const uint64_t kNssCacheSize = 2048;

// Passwd buffer size. We are guaranteed that a single OS Login user will not
// exceed 32k.
static const uint64_t kPasswdBufferSize = 32768;

static NssCache nss_cache(kNssCacheSize);

static pthread_mutex_t cache_mutex = PTHREAD_MUTEX_INITIALIZER;

int main(int argc, char* argv[]) {
  int error_code = 0;
  // Temporary buffer to hold passwd entries before writing.
  char buffer[kPasswdBufferSize];
  struct passwd pwd;

  // Perform the writes under a global lock.
  MutexLock ml(&cache_mutex);
  nss_cache.Reset();

  // Check if there is a cache already.
  struct stat stat_buf;
  bool backup = !stat(kDefaultFilePath, &stat_buf);
  if (backup) {
    // Write a backup file first, in case lookup fails.
    error_code = rename(kDefaultFilePath, kDefaultBackupFilePath);
    if (error_code) {
      openlog("nss_cache_oslogin", LOG_PID, LOG_USER);
      syslog(LOG_ERR, "Could not create backup file.");
      closelog();
      return error_code;
    }
  }

  std::ofstream cache_file(kDefaultFilePath);
  if (cache_file.fail()) {
    openlog("nss_cache_oslogin", LOG_PID, LOG_USER);
    syslog(LOG_ERR, "Failed to open file %s.", kDefaultFilePath);
    closelog();
    return -1;
  }
  chown(kDefaultFilePath, 0, 0);
  chmod(kDefaultFilePath, S_IRUSR | S_IWUSR | S_IROTH);

  while (!nss_cache.OnLastPage() || nss_cache.HasNextPasswd()) {
    BufferManager buffer_manager(buffer, kPasswdBufferSize);
    if (!nss_cache.NssGetpwentHelper(&buffer_manager, &pwd, &error_code)) {
      break;
    }
    cache_file << pwd.pw_name << ":" << pwd.pw_passwd << ":" << pwd.pw_uid
               << ":" << pwd.pw_gid << ":" << pwd.pw_gecos << ":" << pwd.pw_dir
               << ":" << pwd.pw_shell << "\n";
  }
  cache_file.close();

  // Check for errors.
  if (error_code) {
    openlog("nss_cache_oslogin", LOG_PID, LOG_USER);
    if (error_code == ERANGE) {
      syslog(LOG_ERR, "Received unusually large passwd entry.");
    } else if (error_code == EINVAL) {
      syslog(LOG_ERR, "Encountered malformed passwd entry.");
    } else {
      syslog(LOG_ERR, "Unknown error while retrieving passwd entry.");
    }
    // Restore the backup.
    if (backup) {
      if (rename(kDefaultBackupFilePath, kDefaultFilePath)) {
        syslog(LOG_ERR, "Could not restore data from backup file.");
      }
    }
    closelog();
  }

  // Remove the backup file on success.
  if (!error_code && backup) {
    remove(kDefaultBackupFilePath);
  }
  return error_code;
}
