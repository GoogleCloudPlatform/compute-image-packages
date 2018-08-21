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

#ifndef OSLOGIN_COMPAT_H
#define OSLOGIN_COMPAT_H

#ifdef __FreeBSD__

#include <nsswitch.h>

#define DECLARE_NSS_METHOD_TABLE(name, ...)                     \
    static ns_mtab name[] = {__VA_ARGS__};

#define NSS_METHOD(method, func) {                              \
    .database = NSDB_PASSWD,                                    \
    .name = #method,                                            \
    .method = __nss_compat_ ## method,                          \
    .mdata = (void*)func                                        \
}

#define NSS_REGISTER_METHODS(methods) ns_mtab *                 \
nss_module_register (const char *name, unsigned int *size,      \
                        nss_module_unregister_fn *unregister)   \
{                                                               \
    *size = sizeof (methods) / sizeof (methods[0]);             \
    *unregister = NULL;                                         \
    return (methods);                                           \
}

#define NSS_CACHE_OSLOGIN_PATH "/usr/local/etc/oslogin_passwd.cache"
#define K_DEFAULT_FILE_PATH "/usr/local/etc/oslogin_passwd.cache"
#define K_DEFAULT_BACKUP_FILE_PATH "/usr/local/etc/oslogin_passwd.cache.bak"
#define PAM_SYSLOG(pamh, ...) syslog(__VA_ARGS__)
#define DEFAULT_SHELL "/bin/sh"

#else /* __FreeBSD__ */

#include <security/pam_ext.h>

#define DECLARE_NSS_METHOD_TABLE(name, ...)
#define NSS_CACHE_OSLOGIN_PATH "/etc/oslogin_passwd.cache"
#define NSS_METHOD_PROTOTYPE(m)
#define NSS_REGISTER_METHODS(methods)
#define K_DEFAULT_FILE_PATH "/etc/oslogin_passwd.cache"
#define K_DEFAULT_BACKUP_FILE_PATH "/etc/oslogin_passwd.cache.bak"
#define PAM_SYSLOG pam_syslog
#define DEFAULT_SHELL "/bin/bash"

#endif /* __FreeBSD__ */

#endif /* OSLOGIN_COMPAT_H */
