SHELL = /bin/sh

VERSION = 1.5.3

CPPFLAGS = -I/usr/include/json-c
CXXFLAGS = -fPIC -Wall -g
CFLAGS = $(CXXFLAGS) -Wstrict-prototypes

LDFLAGS = -shared -Wl,-soname,$(SONAME)
LDLIBS = -lcurl -ljson-c
PAMLIBS = -lpam $(LDLIBS)

# Paths which should be overrideable.

PREFIX = /usr
LIBDIR = $(PREFIX)/lib
BINDIR = $(PREFIX)/bin
PAMDIR = $(LIBDIR)/security
MANDIR = /usr/share/man

NSS_OSLOGIN_SONAME       = libnss_oslogin.so.2
NSS_CACHE_OSLOGIN_SONAME = libnss_cache_oslogin.so.2

NSS_OSLOGIN              = nss_module/libnss_oslogin-$(VERSION).so
NSS_CACHE_OSLOGIN        = nss_module/libnss_cache_oslogin-$(VERSION).so

PAM_LOGIN                = pam_module/pam_oslogin_login.so
PAM_ADMIN                = pam_module/pam_oslogin_admin.so

BINARIES = google_oslogin_nss_cache google_authorized_keys bin/google_oslogin_control

all : $(NSS_OSLOGIN) $(NSS_CACHE_OSLOGIN) $(PAM_LOGIN) $(PAM_ADMIN) $(BINARIES)

clean :
	rm -f */*.o */*.so google_oslogin_nss_cache google_authorized_keys

.PHONY : all clean install

# NSS modules.

$(NSS_OSLOGIN) : SONAME = $(NSS_OSLOGIN_SONAME)
$(NSS_OSLOGIN) : nss_module/nss_oslogin.o utils/oslogin_utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS) $^ -o $@ $(LDLIBS)

$(NSS_CACHE_OSLOGIN) : SONAME = $(NSS_CACHE_OSLOGIN_SONAME)
$(NSS_CACHE_OSLOGIN) : nss_module/nss_cache_oslogin.o nss_module/compat/getpwent_r.o utils/oslogin_utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS) $^ -o $@ $(LDLIBS)

# PAM modules

$(PAM_LOGIN) : pam_module/pam_oslogin_login.o utils/oslogin_utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -shared $^ -o $@ $(PAMLIBS)

$(PAM_ADMIN) : pam_module/pam_oslogin_admin.o utils/oslogin_utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -shared $^ -o $@ $(PAMLIBS)

# Utilities.

google_authorized_keys : authorized_keys/authorized_keys.o utils/oslogin_utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $^ -o $@ $(LDLIBS)

google_oslogin_nss_cache: nss_cache/nss_cache.o utils/oslogin_utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $^ -o $@ $(LDLIBS)

# Define these to add dependency on header files.

utils/oslogin_utils.o : utils/oslogin_utils.cc utils/oslogin_utils.h

nss_module/nss_cache_oslogin.o : nss_module/nss_cache_oslogin.c nss_module/nss_cache_oslogin.h

install: all
	install -d $(DESTDIR)$(LIBDIR)
	install -d $(DESTDIR)$(PAMDIR)
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(MANDIR)/man8
	install -m 0644 -t $(DESTDIR)$(LIBDIR) $(NSS_OSLOGIN) $(NSS_CACHE_OSLOGIN)
	install -m 0644 -t $(DESTDIR)$(PAMDIR) $(PAM_ADMIN) $(PAM_LOGIN)
	install -m 0755 -t $(DESTDIR)$(BINDIR) $(BINARIES)
	install -m 0644 -t $(DESTDIR)$(MANDIR)/man8 nss_module/nss-oslogin.8 nss_module/nss-cache-oslogin.8
	gzip -9 $(DESTDIR)$(MANDIR)/man8/nss-oslogin.8
	gzip -9 $(DESTDIR)$(MANDIR)/man8/nss-cache-oslogin.8
	ln -sf nss-oslogin.8.gz               $(DESTDIR)$(MANDIR)/man8/$(NSS_OSLOGIN_SONAME).8.gz
	ln -sf nss-cache-oslogin.8.gz         $(DESTDIR)$(MANDIR)/man8/$(NSS_CACHE_OSLOGIN_SONAME).8.gz
	ln -sf $(notdir $(NSS_OSLOGIN))       $(DESTDIR)$(LIBDIR)/$(NSS_OSLOGIN_SONAME)
	ln -sf $(notdir $(NSS_CACHE_OSLOGIN)) $(DESTDIR)$(LIBDIR)/$(NSS_CACHE_OSLOGIN_SONAME)
ifdef INSTALL_SELINUX
	install -d $(DESTDIR)/usr/share/selinux/packages
	install -m 0644 -t $(DESTDIR)/usr/share/selinux/packages policy/oslogin.pp
endif
