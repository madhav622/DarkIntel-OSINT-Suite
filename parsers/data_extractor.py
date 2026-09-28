import re

class DarknetIntelExtractor:
    def extract_pgp_keys(self, text):
        pgp_pattern = r'-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----'
        return re.findall(pgp_pattern, text)

    def extract_crypto_wallets(self, text):
        btc_pattern = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\bbc1[qzm3cjoy2526qch7w93deffzzpd52326w93def]{38,59}\b'
        xmr_pattern = r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b'
        return {
            'btc': list(set(re.findall(btc_pattern, text))),
            'xmr': list(set(re.findall(xmr_pattern, text)))
        }

    def extract_geo_mentions(self, text):
        geo_keywords = ['dead drop', 'coordinates', 'latitude', 'drop zone', 'location', 'shipping']
        found = []
        for line in text.split('\n'):
            if any(kw in line.lower() for kw in geo_keywords):
                found.append(line.strip())
        return found
