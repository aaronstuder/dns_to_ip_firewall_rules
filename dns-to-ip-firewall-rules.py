#!/usr/bin/env python
"""Dynamic dns to ip address firewall rule creator.

Resolve dynamic dns names into ips and automatically create/destroy
firewall rules. Script requires to run as super user in order to be able to
create the firewall rules.


Requirements:
    The following packages should be installed and enabled before attempting to
    run the script

    Fedora based:
        bind-utils, firewalld

    Ubuntu based:
        dnsutils , ufw

Example:
    To manually run the script

        $ python dns_to_ip_firewall-rules.py

Todo:
    * Fedora based firewall rule creation.
    * Debian firewall rule creation
    * Add cron setup instructions to automate the running of the script.
    * Ability to set custom ports per host.

Author:
    Rodrigo Hissam
"""

import re
import os.path
import time
import datetime
import sys

from subprocess import Popen, PIPE
from platform import linux_distribution


# Functions
def main():
    """Main entry point for the script."""
    # Variables
    #
    # Config your domains their ports and the protocol needed per port. If you
    # want both udp and tcp protocols for the port enter 'both' for protocol
    # type.
    # Example: domain with its ports and protocol:
    #   {
    #    'name': 'example.com',
    #    'ports': [
    #       (53, 'udp'),
    #       (22, 'both'),
    #       (80, 'tcp')
    #       ]
    #   },
    dynamic_domains = [
        {
         'name': 'google.com',
         'ports': [
            (53, 'udp'),
            (22, 'both'),
            (80, 'tcp')
            ]
        },
        {
         'name': 'example.com',
         'ports': [
            (53, 'udp'),
            (22, 'both'),
            (80, 'tcp')
            ]
        },
        {
         'name': 'mangolassi.it',
         'ports': [
            (53, 'both'),
            (443, 'tcp')
         ]
        }
    ]
    # Getting linux distro
    distro = linux_distribution()[0]
    # Script start
    for domain in dynamic_domains:
        current_ip = get_current_ip(domain['name'])
        if os.path.isfile(domain['name']):
            old_ip = get_logged_ip(domain['name'])
            if not current_ip == old_ip:
                delete_firewall_rule(distro, old_ip, domain['ports'])
                create_firewall_rule(distro, current_ip, domain['ports'])
                print("\nAdding {} ip {} - removing {}".format
                      (domain['name'], current_ip, old_ip))
                create_hostname_ip_log(domain['name'], current_ip)
            else:
                print("\nSame ip address nothing to do")
        else:
            create_hostname_ip_log(domain['name'], current_ip)
            create_firewall_rule(distro, current_ip, domain['ports'])
            print("\nAdding to firewall")

        print("{0} - {1}".format(domain['name'], current_ip))
    print("\n")


def get_current_ip(domain):
    """Return the ip after resolving 'host hostame' in the shell."""
    response = Popen(["host", domain], stdout=PIPE)
    response = response.communicate()[0].decode("utf-8")
    response = re.search('^.+?(?=\\n)', response)
    response = response.group(0)
    ip = re.search('\d+.\d+.\d+.\d+$', response)
    return ip.group(0)


def create_hostname_ip_log(domain, ip):
    """Create a file with the ip of the resolved domain."""
    file = open(domain, "w")
    file.write("{0}".format(ip))
    file.close()


def get_logged_ip(domain):
    """Get logged ip for requested domain."""
    file = open(domain, 'r')
    logged_ip = file.read()
    file.close()
    return logged_ip


def create_firewall_rule(distro, ip, ports):
    """Create firewall rule based on newest ip of dynamic domain."""
    if 'Ubuntu' in distro:
        for port in ports:
            if port[1] == 'both':
                Popen(
                 ["ufw", "allow", "from", ip, "to", "any", "port",
                 str(port[0])], stdout=PIPE, stderr=PIPE)
            else:
                Popen(
                  ["ufw", "allow", "from", ip, "to", "any", "port",
                   str(port[0]), "proto", port[1]], stdout=PIPE, stderr=PIPE)
            # ufw freaks out when adding rules too fast
            time.sleep(.5)
    elif 'Cent' in distro or 'Fedora' in distro or 'Red' in distro:
        print("")


def delete_firewall_rule(distro, ip, ports):
    """Delete firewall rule in order to add new ip from dynamic domain."""
    if 'Ubuntu' in distro:
        for port in ports:
            if port[1] == 'both':
                Popen(
                 ["ufw", "delete", "allow", "from", ip, "to", "any", "port",
                  str(port[0])], stdout=PIPE, stderr=PIPE)
            else:
                Popen(
                  ["ufw", "delete", "allow", "from", ip, "to", "any", "port",
                   str(port[0]), "proto", port[1]], stdout=PIPE, stderr=PIPE)
            # ufw freaks out when deleting rules too fast
            time.sleep(.5)
    elif 'Cent' in distro or 'Fed' in distro or 'Red' in distro:
        print("")


if __name__ == '__main__':
    sys.exit(main())
