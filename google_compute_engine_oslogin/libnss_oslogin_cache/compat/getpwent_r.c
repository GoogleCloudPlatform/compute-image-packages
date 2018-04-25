/*
 * ----------------------------------------------------------------------
 *  Copyright © 2005-2014 Rich Felker, et al.
 *
 *  Permission is hereby granted, free of charge, to any person obtaining
 *  a copy of this software and associated documentation files (the
 *  "Software"), to deal in the Software without restriction, including
 *  without limitation the rights to use, copy, modify, merge, publish,
 *  distribute, sublicense, and/or sell copies of the Software, and to
 *  permit persons to whom the Software is furnished to do so, subject to
 *  the following conditions:
 *
 *  The above copyright notice and this permission notice shall be
 *  included in all copies or substantial portions of the Software.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 *  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 *  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 *  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 *  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 *  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 *  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *  ----------------------------------------------------------------------
 *
 *  Adapted from http://www.musl-libc.org/ for libnss-cache
 *  Copyright © 2015 Kevin Bowling <k@kev009.com>
 */

#include <sys/param.h>

#ifdef BSD

#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>

static unsigned atou(char **s)
{
	unsigned x;
	for (x=0; **s-'0'<10U; ++*s) x=10*x+(**s-'0');
	return x;
}

int fgetpwent_r(FILE *f, struct passwd *pw, char *line, size_t size, struct passwd **res)
{
	char *s;
	int rv = 0;
	for (;;) {
		line[size-1] = '\xff';
		if ( (fgets(line, size, f) == NULL) || ferror(f) || line[size-1] != '\xff' ) {
			rv = (line[size-1] != '\xff') ? ERANGE : ENOENT;
			line = 0;
			pw = 0;
			break;
		}
		line[strcspn(line, "\n")] = 0;

		s = line;
		pw->pw_name = s++;
		if (!(s = strchr(s, ':'))) continue;

		*s++ = 0; pw->pw_passwd = s;
		if (!(s = strchr(s, ':'))) continue;

		*s++ = 0; pw->pw_uid = atou(&s);
		if (*s != ':') continue;

		*s++ = 0; pw->pw_gid = atou(&s);
		if (*s != ':') continue;

		*s++ = 0; pw->pw_gecos = s;
		if (!(s = strchr(s, ':'))) continue;

		*s++ = 0; pw->pw_dir = s;
		if (!(s = strchr(s, ':'))) continue;

		*s++ = 0; pw->pw_shell = s;
		break;
	}
	*res = pw;
	if (rv) errno = rv;
	return rv;
}

#endif // ifdef BSD
