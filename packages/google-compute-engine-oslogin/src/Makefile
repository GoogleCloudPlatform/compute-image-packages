SHELL = /bin/sh
TOPDIR = $(realpath ..)

VERSION = 1.5.3

CPPFLAGS = -Iinclude -I/usr/include/json-c
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

NSS_OSLOGIN              = libnss_oslogin-$(VERSION).so
NSS_CACHE_OSLOGIN        = libnss_cache_oslogin-$(VERSION).so

PAM_LOGIN                = pam_oslogin_login.so
PAM_ADMIN                = pam_oslogin_admin.so

BINARIES = google_oslogin_nss_cache google_authorized_keys

all : $(NSS_OSLOGIN) $(NSS_CACHE_OSLOGIN) $(PAM_LOGIN) $(PAM_ADMIN) $(BINARIES)

clean :
	rm -f $(BINARIES)
	find . -type f \( -iname '*.o' -o '*.so' \) -delete

.PHONY : all clean install

# NSS modules.

$(NSS_OSLOGIN) : SONAME = $(NSS_OSLOGIN_SONAME)
$(NSS_OSLOGIN) : nss/nss_oslogin.o utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS) $^ -o $@ $(LDLIBS)

$(NSS_CACHE_OSLOGIN) : SONAME = $(NSS_CACHE_OSLOGIN_SONAME)
$(NSS_CACHE_OSLOGIN) : nss/nss_cache_oslogin.o nss/compat/getpwent_r.o utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(LDFLAGS) $^ -o $@ $(LDLIBS)

# PAM modules

$(PAM_LOGIN) : pam/pam_oslogin_login.o utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -shared $^ -o $@ $(PAMLIBS)

$(PAM_ADMIN) : pam/pam_oslogin_admin.o utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) -shared $^ -o $@ $(PAMLIBS)

# Utilities.

google_authorized_keys : authorized_keys/authorized_keys.o utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $^ -o $@ $(LDLIBS)

google_oslogin_nss_cache: cache_refresh/cache_refresh.o utils.o
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $^ -o $@ $(LDLIBS)

install: all
	install -d $(DESTDIR)$(LIBDIR)
	install -d $(DESTDIR)$(PAMDIR)
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(MANDIR)/man8
	install -m 0644 -t $(DESTDIR)$(LIBDIR) $(NSS_OSLOGIN) $(NSS_CACHE_OSLOGIN)
	ln -sf $(NSS_OSLOGIN)         $(DESTDIR)$(LIBDIR)/$(NSS_OSLOGIN_SONAME)
	ln -sf $(NSS_CACHE_OSLOGIN)   $(DESTDIR)$(LIBDIR)/$(NSS_CACHE_OSLOGIN_SONAME)
	install -m 0644 -t $(DESTDIR)$(PAMDIR) $(PAM_ADMIN) $(PAM_LOGIN)
	install -m 0755 -t $(DESTDIR)$(BINDIR) $(BINARIES) $(TOPDIR)/google_oslogin_control
	install -m 0644 -t $(DESTDIR)$(MANDIR)/man8 $(TOPDIR)/man/nss-oslogin.8 $(TOPDIR)/man/nss-cache-oslogin.8
	gzip -9 $(DESTDIR)$(MANDIR)/man8/nss-oslogin.8
	gzip -9 $(DESTDIR)$(MANDIR)/man8/nss-cache-oslogin.8
	ln -sf nss-oslogin.8.gz       $(DESTDIR)$(MANDIR)/man8/$(NSS_OSLOGIN_SONAME).8.gz
	ln -sf nss-cache-oslogin.8.gz $(DESTDIR)$(MANDIR)/man8/$(NSS_CACHE_OSLOGIN_SONAME).8.gz
ifdef INSTALL_SELINUX
	install -d $(DESTDIR)/usr/share/selinux/packages
	install -m 0644 -t $(DESTDIR)/usr/share/selinux/packages $(TOPDIR)/selinux/oslogin.pp
endif
