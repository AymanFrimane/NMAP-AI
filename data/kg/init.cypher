// NMAP-AI Knowledge Graph Initialization Script
// Creates nodes and relationships for nmap options

// Clear existing data (for development only)
MATCH (n) DETACH DELETE n;

// Create Option nodes for Scan Types
CREATE (sS:Option {
    name: '-sS',
    category: 'SCAN_TYPE',
    description: 'TCP SYN scan (stealth scan)',
    requires_root: true,
    requires_args: false,
    example: 'nmap -sS 192.168.1.1'
})

CREATE (sT:Option {
    name: '-sT',
    category: 'SCAN_TYPE',
    description: 'TCP connect scan',
    requires_root: false,
    requires_args: false,
    example: 'nmap -sT 192.168.1.1'
})

CREATE (sU:Option {
    name: '-sU',
    category: 'SCAN_TYPE',
    description: 'UDP scan',
    requires_root: true,
    requires_args: false,
    example: 'nmap -sU 192.168.1.1'
})

CREATE (sn:Option {
    name: '-sn',
    category: 'DISCOVERY',
    description: 'Ping scan (no port scan)',
    requires_root: false,
    requires_args: false,
    example: 'nmap -sn 192.168.1.0/24'
})

// Port Specification
CREATE (p:Option {
    name: '-p',
    category: 'PORT_SPEC',
    description: 'Port specification',
    requires_root: false,
    requires_args: true,
    example: 'nmap -p 80,443 192.168.1.1'
})

CREATE (pAll:Option {
    name: '-p-',
    category: 'PORT_SPEC',
    description: 'Scan all 65535 ports',
    requires_root: false,
    requires_args: false,
    example: 'nmap -p- 192.168.1.1'
})

CREATE (F:Option {
    name: '-F',
    category: 'PORT_SPEC',
    description: 'Fast scan (100 common ports)',
    requires_root: false,
    requires_args: false,
    example: 'nmap -F 192.168.1.1'
})

CREATE (topPorts:Option {
    name: '--top-ports',
    category: 'PORT_SPEC',
    description: 'Scan N most common ports',
    requires_root: false,
    requires_args: true,
    example: 'nmap --top-ports 10 192.168.1.1'
})

// Service/Version Detection
CREATE (sV:Option {
    name: '-sV',
    category: 'SERVICE_DETECTION',
    description: 'Version detection',
    requires_root: false,
    requires_args: false,
    example: 'nmap -sV 192.168.1.1'
})

// OS Detection
CREATE (O:Option {
    name: '-O',
    category: 'OS_DETECTION',
    description: 'OS detection',
    requires_root: true,
    requires_args: false,
    example: 'nmap -O 192.168.1.1'
})

// Timing Templates
CREATE (T0:Option {name: '-T0', category: 'TIMING', description: 'Paranoid timing', requires_root: false, requires_args: false, example: 'nmap -T0 192.168.1.1'})
CREATE (T1:Option {name: '-T1', category: 'TIMING', description: 'Sneaky timing', requires_root: false, requires_args: false, example: 'nmap -T1 192.168.1.1'})
CREATE (T2:Option {name: '-T2', category: 'TIMING', description: 'Polite timing', requires_root: false, requires_args: false, example: 'nmap -T2 192.168.1.1'})
CREATE (T3:Option {name: '-T3', category: 'TIMING', description: 'Normal timing', requires_root: false, requires_args: false, example: 'nmap -T3 192.168.1.1'})
CREATE (T4:Option {name: '-T4', category: 'TIMING', description: 'Aggressive timing', requires_root: false, requires_args: false, example: 'nmap -T4 192.168.1.1'})
CREATE (T5:Option {name: '-T5', category: 'TIMING', description: 'Insane timing', requires_root: false, requires_args: false, example: 'nmap -T5 192.168.1.1'})

// Scripts
CREATE (script:Option {
    name: '--script',
    category: 'SCRIPTING',
    description: 'Run NSE scripts',
    requires_root: false,
    requires_args: true,
    example: 'nmap --script vuln 192.168.1.1'
})

CREATE (scriptArgs:Option {
    name: '--script-args',
    category: 'SCRIPTING',
    description: 'Script arguments',
    requires_root: false,
    requires_args: true,
    example: 'nmap --script-args user=foo 192.168.1.1'
})

// Output Options
CREATE (oX:Option {name: '-oX', category: 'OUTPUT', description: 'XML output', requires_root: false, requires_args: true, example: 'nmap -oX scan.xml 192.168.1.1'})
CREATE (oN:Option {name: '-oN', category: 'OUTPUT', description: 'Normal output', requires_root: false, requires_args: true, example: 'nmap -oN scan.txt 192.168.1.1'})
CREATE (oG:Option {name: '-oG', category: 'OUTPUT', description: 'Grepable output', requires_root: false, requires_args: true, example: 'nmap -oG scan.gnmap 192.168.1.1'})

// Miscellaneous
CREATE (traceroute:Option {
    name: '--traceroute',
    category: 'MISC',
    description: 'Trace path to host',
    requires_root: false,
    requires_args: false,
    example: 'nmap --traceroute 192.168.1.1'
})

CREATE (ipv6:Option {
    name: '-6',
    category: 'MISC',
    description: 'IPv6 scanning',
    requires_root: false,
    requires_args: false,
    example: 'nmap -6 ::1'
})

CREATE (A:Option {
    name: '-A',
    category: 'AGGRESSIVE',
    description: 'Aggressive scan (OS, version, scripts, traceroute)',
    requires_root: true,
    requires_args: false,
    example: 'nmap -A 192.168.1.1'
})

CREATE (v:Option {
    name: '-v',
    category: 'OUTPUT',
    description: 'Verbose output',
    requires_root: false,
    requires_args: false,
    example: 'nmap -v 192.168.1.1'
})

CREATE (vv:Option {
    name: '-vv',
    category: 'OUTPUT',
    description: 'Very verbose output',
    requires_root: false,
    requires_args: false,
    example: 'nmap -vv 192.168.1.1'
})

CREATE (Pn:Option {
    name: '-Pn',
    category: 'HOST_DISCOVERY',
    description: 'Skip host discovery',
    requires_root: false,
    requires_args: false,
    example: 'nmap -Pn 192.168.1.1'
})

CREATE (n:Option {
    name: '-n',
    category: 'DNS',
    description: 'No DNS resolution',
    requires_root: false,
    requires_args: false,
    example: 'nmap -n 192.168.1.1'
})

CREATE (R:Option {
    name: '-R',
    category: 'DNS',
    description: 'Always do DNS resolution',
    requires_root: false,
    requires_args: false,
    example: 'nmap -R 192.168.1.1'
})

// ============ CONFLICT RELATIONSHIPS ============

// Scan type conflicts (mutually exclusive)
MATCH (sS:Option {name: '-sS'})
MATCH (sT:Option {name: '-sT'})
MATCH (sU:Option {name: '-sU'})
MATCH (sn:Option {name: '-sn'})

CREATE (sS)-[:CONFLICTS_WITH]->(sT)
CREATE (sS)-[:CONFLICTS_WITH]->(sU)
CREATE (sS)-[:CONFLICTS_WITH]->(sn)

CREATE (sT)-[:CONFLICTS_WITH]->(sS)
CREATE (sT)-[:CONFLICTS_WITH]->(sU)
CREATE (sT)-[:CONFLICTS_WITH]->(sn)

CREATE (sU)-[:CONFLICTS_WITH]->(sS)
CREATE (sU)-[:CONFLICTS_WITH]->(sT)
CREATE (sU)-[:CONFLICTS_WITH]->(sn)

CREATE (sn)-[:CONFLICTS_WITH]->(sS)
CREATE (sn)-[:CONFLICTS_WITH]->(sT)
CREATE (sn)-[:CONFLICTS_WITH]->(sU);

// Port specification conflicts
MATCH (p:Option {name: '-p'})
MATCH (F:Option {name: '-F'})
MATCH (pAll:Option {name: '-p-'})
MATCH (topPorts:Option {name: '--top-ports'})

CREATE (p)-[:CONFLICTS_WITH]->(F)
CREATE (F)-[:CONFLICTS_WITH]->(p)
CREATE (F)-[:CONFLICTS_WITH]->(pAll)
CREATE (pAll)-[:CONFLICTS_WITH]->(F)
CREATE (pAll)-[:CONFLICTS_WITH]->(topPorts)
CREATE (topPorts)-[:CONFLICTS_WITH]->(pAll);

// -sn conflicts with port specification
MATCH (sn:Option {name: '-sn'})
MATCH (p:Option {name: '-p'})
CREATE (sn)-[:CONFLICTS_WITH]->(p)
CREATE (p)-[:CONFLICTS_WITH]->(sn);

// Timing conflicts (mutually exclusive)
MATCH (T0:Option {name: '-T0'})
MATCH (T1:Option {name: '-T1'})
MATCH (T2:Option {name: '-T2'})
MATCH (T3:Option {name: '-T3'})
MATCH (T4:Option {name: '-T4'})
MATCH (T5:Option {name: '-T5'})

CREATE (T0)-[:CONFLICTS_WITH]->(T1)
CREATE (T0)-[:CONFLICTS_WITH]->(T2)
CREATE (T0)-[:CONFLICTS_WITH]->(T3)
CREATE (T0)-[:CONFLICTS_WITH]->(T4)
CREATE (T0)-[:CONFLICTS_WITH]->(T5)

CREATE (T1)-[:CONFLICTS_WITH]->(T0)
CREATE (T1)-[:CONFLICTS_WITH]->(T2)
CREATE (T1)-[:CONFLICTS_WITH]->(T3)
CREATE (T1)-[:CONFLICTS_WITH]->(T4)
CREATE (T1)-[:CONFLICTS_WITH]->(T5)

CREATE (T2)-[:CONFLICTS_WITH]->(T0)
CREATE (T2)-[:CONFLICTS_WITH]->(T1)
CREATE (T2)-[:CONFLICTS_WITH]->(T3)
CREATE (T2)-[:CONFLICTS_WITH]->(T4)
CREATE (T2)-[:CONFLICTS_WITH]->(T5)

CREATE (T3)-[:CONFLICTS_WITH]->(T0)
CREATE (T3)-[:CONFLICTS_WITH]->(T1)
CREATE (T3)-[:CONFLICTS_WITH]->(T2)
CREATE (T3)-[:CONFLICTS_WITH]->(T4)
CREATE (T3)-[:CONFLICTS_WITH]->(T5)

CREATE (T4)-[:CONFLICTS_WITH]->(T0)
CREATE (T4)-[:CONFLICTS_WITH]->(T1)
CREATE (T4)-[:CONFLICTS_WITH]->(T2)
CREATE (T4)-[:CONFLICTS_WITH]->(T3)
CREATE (T4)-[:CONFLICTS_WITH]->(T5)

CREATE (T5)-[:CONFLICTS_WITH]->(T0)
CREATE (T5)-[:CONFLICTS_WITH]->(T1)
CREATE (T5)-[:CONFLICTS_WITH]->(T2)
CREATE (T5)-[:CONFLICTS_WITH]->(T3)
CREATE (T5)-[:CONFLICTS_WITH]->(T4);

// DNS resolution conflicts
MATCH (n:Option {name: '-n'})
MATCH (R:Option {name: '-R'})
CREATE (n)-[:CONFLICTS_WITH]->(R)
CREATE (R)-[:CONFLICTS_WITH]->(n);

// Pn conflicts with sn
MATCH (Pn:Option {name: '-Pn'})
MATCH (sn:Option {name: '-sn'})
CREATE (Pn)-[:CONFLICTS_WITH]->(sn)
CREATE (sn)-[:CONFLICTS_WITH]->(Pn);

// ============ DEPENDENCY RELATIONSHIPS ============

// --script-args requires --script
MATCH (scriptArgs:Option {name: '--script-args'})
MATCH (script:Option {name: '--script'})
CREATE (scriptArgs)-[:REQUIRES]->(script);

// ============ COMMON SERVICES ============

CREATE (service_ssh:Service {name: 'SSH', port: 22, protocol: 'TCP', description: 'Secure Shell'})
CREATE (service_http:Service {name: 'HTTP', port: 80, protocol: 'TCP', description: 'Web Server'})
CREATE (service_https:Service {name: 'HTTPS', port: 443, protocol: 'TCP', description: 'Secure Web Server'})
CREATE (service_ftp:Service {name: 'FTP', port: 21, protocol: 'TCP', description: 'File Transfer Protocol'})
CREATE (service_smtp:Service {name: 'SMTP', port: 25, protocol: 'TCP', description: 'Email Server'})
CREATE (service_dns:Service {name: 'DNS', port: 53, protocol: 'UDP', description: 'Domain Name System'})
CREATE (service_mysql:Service {name: 'MySQL', port: 3306, protocol: 'TCP', description: 'MySQL Database'})
CREATE (service_rdp:Service {name: 'RDP', port: 3389, protocol: 'TCP', description: 'Remote Desktop'})
CREATE (service_snmp:Service {name: 'SNMP', port: 161, protocol: 'UDP', description: 'Network Management'})
CREATE (service_telnet:Service {name: 'Telnet', port: 23, protocol: 'TCP', description: 'Telnet'});

// Verify creation
MATCH (n) RETURN labels(n) as type, count(n) as count;
