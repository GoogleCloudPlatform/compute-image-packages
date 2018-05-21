import os
import platform

def linux_distribution():
    """Determine the distribution by reading /etc/os-release"""
    distro_name = '',
    distro_version = ''
    release_file = '/etc/os-release'
    if os.path.exists(release_file):
        with open(release_file) as os_release:
            for line in os_release.readlines():
                if line.strip().startswith('ID='):
                    distro_name = line.split('=')[-1]
                    distro_name = distro_name.replace('"', '')
                if line.strip().startswith('VERSION_ID='):
                    # Lets hope for the best that distros stay consistent ;)
                    distro_version = line.split('=')[-1]
                    distro_version = distro_version.replace('"', '')
    return (distro_name, distro_version, platform.machine())
                
