import re

def extract_entities(html_content):
    if not html_content:
        return {"crypto_wallets": [], "pgp_keys": [], "geo_coordinates": []}

    # Regex Patterns for Crypto Wallets
    btc_pattern = r'\b(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b'
    eth_pattern = r'\b0x[a-fA-F0-9]{40}\b'
    xmr_pattern = r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'
    
    # Regex Pattern for PGP Keys
    pgp_pattern = r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----'
    
    # Regex Pattern for Coordinates
    geo_pattern = r'\b[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)\b'

    btc_wallets = re.findall(btc_pattern, html_content)
    btc_wallets = [w[0] if isinstance(w, tuple) else w for w in btc_wallets]
    eth_wallets = re.findall(eth_pattern, html_content)
    xmr_wallets = re.findall(xmr_pattern, html_content)
    
    crypto_wallets = list(set(btc_wallets + eth_wallets + xmr_wallets))
    pgp_keys = re.findall(pgp_pattern, html_content)
    
    geo_matches = re.findall(geo_pattern, html_content)
    geo_coordinates = []
    for g in geo_matches:
        if isinstance(g, tuple):
            geo_coordinates.append(g[0])
            
    return {
        "crypto_wallets": crypto_wallets,
        "pgp_keys": pgp_keys,
        "geo_coordinates": list(set(geo_coordinates))
    }
