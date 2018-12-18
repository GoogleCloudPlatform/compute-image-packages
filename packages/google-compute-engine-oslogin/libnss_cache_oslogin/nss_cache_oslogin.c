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

// An NSS module which adds supports for file /etc/oslogin_passwd.cache

#include "nss_cache_oslogin.h"
#include "../compat.h"

#include <sys/mman.h>

// Locking implementation: use pthreads.
#include <pthread.h>
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
#define NSS_CACHE_OSLOGIN_LOCK() \
  do {                           \
    pthread_mutex_lock(&mutex);  \
  } while (0)
#define NSS_CACHE_OSLOGIN_UNLOCK() \
  do {                             \
    pthread_mutex_unlock(&mutex);  \
  } while (0)

static FILE *p_file = NULL;
static char p_filename[NSS_CACHE_OSLOGIN_PATH_LENGTH] = NSS_CACHE_OSLOGIN_PATH;
#ifdef BSD
extern int fgetpwent_r(FILE *, struct passwd *, char *, size_t,
                       struct passwd **);
#endif  // ifdef BSD

/* Common return code routine for all *ent_r_locked functions.
 * We need to return TRYAGAIN if the underlying files guy raises ERANGE,
 * so that our caller knows to try again with a bigger buffer.
 */

static inline enum nss_status _nss_cache_oslogin_ent_bad_return_code(
    int errnoval) {
  enum nss_status ret;

  switch (errnoval) {
    case ERANGE:
      DEBUG("ERANGE: Try again with a bigger buffer\n");
      ret = NSS_STATUS_TRYAGAIN;
      break;
    case ENOENT:
    default:
      DEBUG("ENOENT or default case: Not found\n");
      ret = NSS_STATUS_NOTFOUND;
  };
  return ret;
}

//
// Binary search routines below here
//

int _nss_cache_oslogin_bsearch2_compare(const void *key, const void *value) {
  struct nss_cache_oslogin_args *args = (struct nss_cache_oslogin_args *)key;
  const char *value_text = (const char *)value;

  // Using strcmp as the generation of the index sorts without
  // locale awareness.
  return strcmp(args->lookup_key, value_text);
}

enum nss_status _nss_cache_oslogin_bsearch2(struct nss_cache_oslogin_args *args,
                                            int *errnop) {
  enum nss_cache_oslogin_match (*lookup)(
      FILE *, struct nss_cache_oslogin_args *) = args->lookup_function;
  FILE *file = NULL;
  FILE *system_file_stream = NULL;
  struct stat system_file;
  struct stat sorted_file;
  enum nss_status ret = 100;
  long offset = 0;
  void *mapped_data = NULL;

  file = fopen(args->sorted_filename, "r");
  if (file == NULL) {
    DEBUG("error opening %s\n", args->sorted_filename);
    return NSS_STATUS_UNAVAIL;
  }

  // if the sorted file is older than the system file, do not risk stale
  // data and abort
  // TODO(vasilios):  should be a compile or runtime option
  if (stat(args->system_filename, &system_file) != 0) {
    DEBUG("failed to stat %s\n", args->system_filename);
    fclose(file);
    return NSS_STATUS_UNAVAIL;
  }
  if (fstat(fileno(file), &sorted_file) != 0) {
    DEBUG("failed to stat %s\n", args->sorted_filename);
    fclose(file);
    return NSS_STATUS_UNAVAIL;
  }
  if (difftime(system_file.st_mtime, sorted_file.st_mtime) > 0) {
    DEBUG("%s may be stale, aborting lookup\n", args->sorted_filename);
    fclose(file);
    return NSS_STATUS_UNAVAIL;
  }

  mapped_data =
      mmap(NULL, sorted_file.st_size, PROT_READ, MAP_PRIVATE, fileno(file), 0);
  if (mapped_data == MAP_FAILED) {
    DEBUG("mmap failed\n");
    fclose(file);
    return NSS_STATUS_UNAVAIL;
  }

  const char *data = (const char *)mapped_data;
  while (*data != '\n') {
    ++data;
  }
  long entry_size = data - (const char *)mapped_data + 1;
  long entry_count = sorted_file.st_size / entry_size;

  void *entry = bsearch(args, mapped_data, entry_count, entry_size,
                        &_nss_cache_oslogin_bsearch2_compare);
  if (entry != NULL) {
    const char *entry_text = entry;
    sscanf(entry_text + strlen(entry_text) + 1, "%ld", &offset);
  }

  if (munmap(mapped_data, sorted_file.st_size) == -1) {
    DEBUG("munmap failed\n");
  }
  fclose(file);

  if (entry == NULL) {
    return NSS_STATUS_NOTFOUND;
  }

  system_file_stream = fopen(args->system_filename, "r");
  if (system_file_stream == NULL) {
    DEBUG("error opening %s\n", args->system_filename);
    return NSS_STATUS_UNAVAIL;
  }

  if (fseek(system_file_stream, offset, SEEK_SET) != 0) {
    DEBUG("fseek fail\n");
    return NSS_STATUS_UNAVAIL;
  }

  switch (lookup(system_file_stream, args)) {
    case NSS_CACHE_OSLOGIN_EXACT:
      ret = NSS_STATUS_SUCCESS;
      break;
    case NSS_CACHE_OSLOGIN_ERROR:
      if (errno == ERANGE) {
        // let the caller retry
        *errnop = errno;
        ret = _nss_cache_oslogin_ent_bad_return_code(*errnop);
      }
      break;
    default:
      ret = NSS_STATUS_UNAVAIL;
      break;
  }

  fclose(system_file_stream);
  return ret;
}

//
// Routines for passwd map defined below here
//

// _nss_cache_oslogin_setpwent_path()
// Helper function for testing

extern char *_nss_cache_oslogin_setpwent_path(const char *path) {
  DEBUG("%s %s\n", "Setting p_filename to", path);
  return strncpy(p_filename, path, NSS_CACHE_OSLOGIN_PATH_LENGTH - 1);
}

// _nss_cache_oslogin_pwuid_wrap()
// Internal wrapper for binary searches, using uid-specific calls.

static enum nss_cache_oslogin_match _nss_cache_oslogin_pwuid_wrap(
    FILE *file, struct nss_cache_oslogin_args *args) {
  struct passwd *result = args->lookup_result;
  uid_t *uid = args->lookup_value;

  if (fgetpwent_r(file, result, args->buffer, args->buflen, &result) == 0) {
    if (result->pw_uid == *uid) {
      DEBUG("SUCCESS: found user %d:%s\n", result->pw_uid, result->pw_name);
      return NSS_CACHE_OSLOGIN_EXACT;
    }
    DEBUG("Failed match at uid %d\n", result->pw_uid);
    if (result->pw_uid > *uid) {
      return NSS_CACHE_OSLOGIN_HIGH;
    } else {
      return NSS_CACHE_OSLOGIN_LOW;
    }
  }

  return NSS_CACHE_OSLOGIN_ERROR;
}

// _nss_cache_oslogin_pwnam_wrap()
// Internal wrapper for binary searches, using username-specific calls.

static enum nss_cache_oslogin_match _nss_cache_oslogin_pwnam_wrap(
    FILE *file, struct nss_cache_oslogin_args *args) {
  struct passwd *result = args->lookup_result;
  char *name = args->lookup_value;
  int ret;

  if (fgetpwent_r(file, result, args->buffer, args->buflen, &result) == 0) {
    ret = strcoll(result->pw_name, name);
    if (ret == 0) {
      DEBUG("SUCCESS: found user %s\n", result->pw_name);
      return NSS_CACHE_OSLOGIN_EXACT;
    }
    DEBUG("Failed match at name %s\n", result->pw_name);
    if (ret > 0) {
      return NSS_CACHE_OSLOGIN_HIGH;
    } else {
      return NSS_CACHE_OSLOGIN_LOW;
    }
  }

  return NSS_CACHE_OSLOGIN_ERROR;
}

// _nss_cache_oslogin_setpwent_locked()
// Internal setup routine

static enum nss_status _nss_cache_oslogin_setpwent_locked(void) {
  DEBUG("%s %s\n", "Opening", p_filename);
  p_file = fopen(p_filename, "r");

  if (p_file) {
    return NSS_STATUS_SUCCESS;
  } else {
    return NSS_STATUS_UNAVAIL;
  }
}

// _nss_cache_oslogin_setpwent()
// Called by NSS to open the passwd file
// 'stayopen' parameter is ignored.

enum nss_status _nss_cache_oslogin_setpwent(int stayopen) {
  enum nss_status ret;
  NSS_CACHE_OSLOGIN_LOCK();
  ret = _nss_cache_oslogin_setpwent_locked();
  NSS_CACHE_OSLOGIN_UNLOCK();
  return ret;
}

// _nss_cache_oslogin_endpwent_locked()
// Internal close routine

static enum nss_status _nss_cache_oslogin_endpwent_locked(void) {
  DEBUG("Closing passwd.cache\n");
  if (p_file) {
    fclose(p_file);
    p_file = NULL;
  }
  return NSS_STATUS_SUCCESS;
}

// _nss_cache_oslogin_endpwent()
// Called by NSS to close the passwd file

enum nss_status _nss_cache_oslogin_endpwent(void) {
  enum nss_status ret;
  NSS_CACHE_OSLOGIN_LOCK();
  ret = _nss_cache_oslogin_endpwent_locked();
  NSS_CACHE_OSLOGIN_UNLOCK();
  return ret;
}

// _nss_cache_oslogin_getpwent_r_locked()
// Called internally to return the next entry from the passwd file

static enum nss_status _nss_cache_oslogin_getpwent_r_locked(
    struct passwd *result, char *buffer, size_t buflen, int *errnop) {
  enum nss_status ret = NSS_STATUS_SUCCESS;

  if (p_file == NULL) {
    DEBUG("p_file == NULL, going to setpwent\n");
    ret = _nss_cache_oslogin_setpwent_locked();
  }

  if (ret == NSS_STATUS_SUCCESS) {
    if (fgetpwent_r(p_file, result, buffer, buflen, &result) == 0) {
      DEBUG("Returning user %d:%s\n", result->pw_uid, result->pw_name);
    } else {
      if (errno == ENOENT) {
        errno = 0;
      }
      *errnop = errno;
      ret = _nss_cache_oslogin_ent_bad_return_code(*errnop);
    }
  }

  return ret;
}

// _nss_cache_oslogin_getpwent_r()
// Called by NSS to look up next entry in passwd file

enum nss_status _nss_cache_oslogin_getpwent_r(struct passwd *result,
                                              char *buffer, size_t buflen,
                                              int *errnop) {
  enum nss_status ret;
  NSS_CACHE_OSLOGIN_LOCK();
  ret = _nss_cache_oslogin_getpwent_r_locked(result, buffer, buflen, errnop);
  NSS_CACHE_OSLOGIN_UNLOCK();
  return ret;
}

// _nss_cache_oslogin_getpwuid_r()
// Find a user account by uid

enum nss_status _nss_cache_oslogin_getpwuid_r(uid_t uid, struct passwd *result,
                                              char *buffer, size_t buflen,
                                              int *errnop) {
  char filename[NSS_CACHE_OSLOGIN_PATH_LENGTH];
  struct nss_cache_oslogin_args args;
  enum nss_status ret;

  strncpy(filename, p_filename, NSS_CACHE_OSLOGIN_PATH_LENGTH - 1);
  if (strlen(filename) > NSS_CACHE_OSLOGIN_PATH_LENGTH - 7) {
    DEBUG("filename too long\n");
    return NSS_STATUS_UNAVAIL;
  }
  strncat(filename, ".ixuid", 6);

  args.sorted_filename = filename;
  args.system_filename = p_filename;
  args.lookup_function = _nss_cache_oslogin_pwuid_wrap;
  args.lookup_value = &uid;
  args.lookup_result = result;
  args.buffer = buffer;
  args.buflen = buflen;
  char uid_text[11];
  snprintf(uid_text, sizeof(uid_text), "%d", uid);
  args.lookup_key = uid_text;
  args.lookup_key_length = strlen(uid_text);

  DEBUG("Binary search for uid %d\n", uid);
  NSS_CACHE_OSLOGIN_LOCK();
  ret = _nss_cache_oslogin_bsearch2(&args, errnop);

  if (ret == NSS_STATUS_UNAVAIL) {
    DEBUG("Binary search failed, falling back to full linear search\n");
    ret = _nss_cache_oslogin_setpwent_locked();

    if (ret == NSS_STATUS_SUCCESS) {
      while ((ret = _nss_cache_oslogin_getpwent_r_locked(
          result, buffer, buflen, errnop)) == NSS_STATUS_SUCCESS) {
        if (result->pw_uid == uid) break;
      }
    }
  }

  _nss_cache_oslogin_endpwent_locked();
  NSS_CACHE_OSLOGIN_UNLOCK();

  return ret;
}

// _nss_cache_oslogin_getpwnam_r()
// Find a user account by name

enum nss_status _nss_cache_oslogin_getpwnam_r(const char *name,
                                              struct passwd *result,
                                              char *buffer, size_t buflen,
                                              int *errnop) {
  char *pw_name;
  char filename[NSS_CACHE_OSLOGIN_PATH_LENGTH];
  struct nss_cache_oslogin_args args;
  enum nss_status ret;

  NSS_CACHE_OSLOGIN_LOCK();

  // name is a const char, we need a non-const copy
  pw_name = malloc(strlen(name) + 1);
  if (pw_name == NULL) {
    DEBUG("malloc error\n");
    return NSS_STATUS_UNAVAIL;
  }
  strncpy(pw_name, name, strlen(name) + 1);

  strncpy(filename, p_filename, NSS_CACHE_OSLOGIN_PATH_LENGTH - 1);
  if (strlen(filename) > NSS_CACHE_OSLOGIN_PATH_LENGTH - 8) {
    DEBUG("filename too long\n");
    free(pw_name);
    return NSS_STATUS_UNAVAIL;
  }
  strncat(filename, ".ixname", 7);

  args.sorted_filename = filename;
  args.system_filename = p_filename;
  args.lookup_function = _nss_cache_oslogin_pwnam_wrap;
  args.lookup_value = pw_name;
  args.lookup_result = result;
  args.buffer = buffer;
  args.buflen = buflen;
  args.lookup_key = pw_name;
  args.lookup_key_length = strlen(pw_name);

  DEBUG("Binary search for user %s\n", pw_name);
  ret = _nss_cache_oslogin_bsearch2(&args, errnop);

  if (ret == NSS_STATUS_UNAVAIL) {
    DEBUG("Binary search failed, falling back to full linear search\n");
    ret = _nss_cache_oslogin_setpwent_locked();

    if (ret == NSS_STATUS_SUCCESS) {
      while ((ret = _nss_cache_oslogin_getpwent_r_locked(
          result, buffer, buflen, errnop)) == NSS_STATUS_SUCCESS) {
        if (!strcmp(result->pw_name, name)) break;
      }
    }
  }

  free(pw_name);
  _nss_cache_oslogin_endpwent_locked();
  NSS_CACHE_OSLOGIN_UNLOCK();

  return ret;
}

NSS_METHOD_PROTOTYPE(__nss_compat_getpwnam_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getpwuid_r);
NSS_METHOD_PROTOTYPE(__nss_compat_getpwent_r);
NSS_METHOD_PROTOTYPE(__nss_compat_setpwent);
NSS_METHOD_PROTOTYPE(__nss_compat_endpwent);

DECLARE_NSS_METHOD_TABLE(methods,
    { NSDB_PASSWD, "getpwnam_r", __nss_compat_getpwnam_r,
      (void*)_nss_cache_oslogin_getpwnam_r },
    { NSDB_PASSWD, "getpwuid_r", __nss_compat_getpwuid_r,
      (void*)_nss_cache_oslogin_getpwuid_r },
    { NSDB_PASSWD, "getpwent_r", __nss_compat_getpwent_r,
      (void*)_nss_cache_oslogin_getpwent_r },
    { NSDB_PASSWD, "endpwent",   __nss_compat_endpwent,
      (void*)_nss_cache_oslogin_endpwent },
    { NSDB_PASSWD, "setpwent",   __nss_compat_setpwent,
      (void*)_nss_cache_oslogin_setpwent },
)

NSS_REGISTER_METHODS(methods)
