import socket
import sys

def find_ns_suffix(query, zone_records):
    """
    Return CSV-style string "domain,ip,TYPE" for the longest matching NS suffix,
    or None if no NS suffix matches.
    - query: already-decoded lowercase domain string (e.g. "sub.example.co.il")
    - zone_records: dict where key is domain/suffix (lowercased). Value may be:
        * parsed dict: {'domain','ip','type'}
        * raw string: "domain,ip[:port],TYPE"
    """
    q = query.lower()
    best_line = None
    best_len = 0

    for key, rec in zone_records.items():
        # we only consider suffix entries that start with a dot (e.g. ".co.il")
        if not key.startswith('.'):
            continue

        # normalize record type and build response line
        if isinstance(rec, dict):
            rtype = rec.get('type', '').upper()
            line = f"{rec.get('domain')},{rec.get('ip')},{rtype}"
        else:
            parts = [p.strip() for p in rec.rsplit(',', 2)]
            rtype = parts[-1].upper() if parts else ''
            line = rec

        if rtype != 'NS':
            continue

        # check suffix match and pick the most specific (longest) match
        if q.endswith(key) and len(key) > best_len:
            best_len = len(key)
            best_line = line

    return best_line  # None if not found

if __name__ == '__main__':
    # Checks number of arguments is correct
    if len(sys.argv) != 3:        
        sys.exit(1)
    
    port = int(sys.argv[1])    
    zone_file_name = sys.argv[2]
    
    # Load zone records
    zone_records = {}
    with open(zone_file_name, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # split into three parts (domain, ip[:port], type)
            name, ip_addr, rtype = [p.strip() for p in line.split(',', 2)]
            zone_records[name.lower()] = {
                'domain': name,
                'ip': ip_addr,           
                'type': rtype.upper()    
            }  

    # Set up socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    s.bind(('', port))    

    # Main loop for listening
    while True:
            data, addr = s.recvfrom(1024)  
            response = "non-existent domain"

            # We format the input to match our search keys
            query = data.decode().strip()     
            query_lower = query.lower()
            # make an indexable list 
            items = list(zone_records.items())

            response = "non-existent domain"

            # First check for exact match
            if query_lower in zone_records:
                    rec = zone_records[query_lower]                    
                    response = f"{rec['domain']},{rec['ip']},{rec['type']}"
            else:
                # If not we check for a NS suffix match
                ns_line = find_ns_suffix(query_lower, zone_records)
                if ns_line:
                    response = ns_line
        

            # Sending response back to client
            s.sendto(response.encode(), addr)