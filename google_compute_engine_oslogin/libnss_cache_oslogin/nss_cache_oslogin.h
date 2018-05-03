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
#include <stdlib.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/param.h>
#include <time.h>
#include <unistd.h>

#ifndef NSS_CACHE_OSLOGIN_H
#define NSS_CACHE_OSLOGIN_H

#ifdef DEBUG
#undef DEBUG
#define DEBUG(fmt, args...)                                                    \
  do {                                                                         \
    fprintf(stderr, fmt, ##args);                                              \
  } while (0)
#else
#define DEBUG(fmt, ...)                                                        \
  do {                                                                         \
  } while (0)
#endif /* DEBUG */

#define NSS_CACHE_OSLOGIN_PATH_LENGTH 255
extern char *_nss_cache_oslogin_setpwent_path(const char *path);

enum nss_cache_oslogin_match {
  NSS_CACHE_OSLOGIN_EXACT = 0,
  NSS_CACHE_OSLOGIN_HIGH = 1,
  NSS_CACHE_OSLOGIN_LOW = 2,
  NSS_CACHE_OSLOGIN_ERROR = 3,
};

struct nss_cache_oslogin_args {
  char *system_filename;
  char *sorted_filename;
  void *lookup_function;
  void *lookup_value;
  void *lookup_result;
  char *buffer;
  size_t buflen;
  char *lookup_key;
  size_t lookup_key_length;
};

#endif /* NSS_CACHE_OSLOGIN_H */
