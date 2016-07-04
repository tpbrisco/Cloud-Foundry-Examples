#!/usr/bin/python
#
# Demonstration program to lookup service records for named service, in the indicated domain
# Usage: svc_lookup.py <DNS-SD entry>
#
#

import os, sys
import getopt
import dns.resolver
import dns.flags
import dns.exception

default_domain = ''

def usage():
    print 'Usage: svc_lookup [-d <default domain>]'
    sys.exit(2)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:', ['domain'])
except getopt.GetoptError as err:
    print str(err)
    sys.exit(2)

for o,a in opts:
    if o == '-d' or o == '--debug':
        default_domain = a
    else:
        usage()
        assert False, 'unhandled option'

# Look up remaining arguments as (unicast) DNS-SD entries

# set up resolver, using default_domain if appropriate
resolver = dns.resolver.Resolver()  			# defaults to reading /etc/resolv.conf
resolver.flags = dns.flags.RD
if default_domain != '':
    domain = dns.name.from_text(default_domain)
    if not domain.is_absolute():
        domain = domain.concatenate(dns.name.root)
    resolver.search = [ domain ]

# look up service discovery endpoint - examples from RFC6763 seem to work fine
for svc_lookup_request in args:
    # get main entry, requesting PTR RRs
    try:
        svc_ptrs = resolver.query(svc_lookup_request, dns.rdatatype.PTR, raise_on_no_answer=False)
    except dns.exception.DNSException as e:
        print e.message
        sys.exit(1)
    if svc_ptrs.rrset is None or len(svc_ptrs.rrset) < 1:
        print "%s isn't a service list" % (svc_lookup_request)
        continue

    # look up each PTR, looking for TXT and SRV RRs
    for svc_ptr in svc_ptrs.rrset:
        print "svc_ptr: Class(%s) Type(%s) %s" % \
            ( dns.rdataclass.to_text(svc_ptr.rdclass),
              dns.rdatatype.to_text(svc_ptr.rdtype),
              svc_ptr.to_text())
        # look up SRV record for details about the service
        try:
            srv_defs = resolver.query(svc_ptr.to_text(), dns.rdatatype.SRV, raise_on_no_answer=False)
        except dns.exception.DNSException as e:
            print svc_ptr.to_text(), e.message
            sys.exit(1)
        assert (len(srv_defs.rrset) == 1)
        srv_def = srv_defs.rrset[0]

        # look up TXT record for parameters for the service
        try:
            txt_defs = resolver.query(svc_ptr.to_text(), dns.rdatatype.TXT, raise_on_no_answer=False)
        except dns.exception.DNSException as e:
            # lack of a TXT is unusual, but permitted under RFC6763 sec6.0 and 6.1
            pass
        assert len(txt_defs.rrset) < 2
        if len(txt_defs.rrset) == 1:
            txt_def = txt_defs.rrset[0]
            txt_string = txt_def.to_text()
        else:
            txt_string = ''

        for srv_def in srv_defs.rrset:
            # DEBUG - print out instance information
            print "srv_def: Class(%s) Type(%s) wght(%d) prio(%d) port(%d) %s" % \
                (dns.rdataclass.to_text(srv_def.rdclass),
                 dns.rdatatype.to_text(srv_def.rdtype),
                 srv_def.priority, srv_def.weight, srv_def.port, srv_def.target)
            if len(txt_defs.rrset):
                print "txt_def: Class(%s) Type(%s) %s" % \
                    (dns.rdataclass.to_text(txt_def.rdclass),
                     dns.rdatatype.to_text(txt_def.rdtype),
                     txt_string)

            # get A record associated with srv_def.target
            try:
                srv_a = resolver.query(srv_def.target, dns.rdatatype.A, raise_on_no_answer=False)
            except dns.exception.DNSException as e:
                print srv_def.target,e.message
                sys.exit(2)
            for a_rr in srv_a:
                print svc_lookup_request, srv_def.target, a_rr.to_text(), srv_def.port
            
