# ANT Automobile Document Verification

The service behind [verify.antautomobile.org](https://verify.antautomobile.org/) and [api.antautomobile.org](https://api.antautomobile.org/). The QR code at the bottom of every official letter issued by ANT Automobile points to this service with the document's number.

## How it works

- Every document gets a random number: `ANT-XXXX-XXXX-XXXX-XXXX` (80 bits, Crockford base32). Numbers are not sequential and there is no list of documents.
- The verification page only reveals information to someone who knows the document number or has the file itself: validity status, issuer, signer and issue date.
- When you drop a PDF on the page, its SHA-256 digest is computed in the browser. The file never leaves your machine; only the digest is compared.
- The server stores no PDFs. A record holds the document details, the SHA-256 digest and the file size.
- Statuses: valid, revoked, superseded by a newer document.

The verification page itself is in Turkish.

## API

The same service answers with JSON when the request is for `api.antautomobile.org`. The endpoints are described in [`api/swagger.yaml`](api/swagger.yaml) (Swagger 2.0).

| Request | Response |
|---|---|
| `GET /v1/verify/<NO>` | Status, issuer, signer, date |
| `GET /v1/verify/<NO>?sha256=<hex>` | The above plus `file_matches` |
| `GET /v1/verify?sha256=<hex>` | The document whose digest matches |

## Files

| Path | Contents |
|---|---|
| `server.py` | Service and command line tool (Python standard library only) |
| `api/swagger.yaml`, `api/ui/` | API description and Swagger UI |
| `nginx/` | Example reverse proxy configuration and rate limit |
| `systemd/` | Service unit |
| `test-sayfa.py` | Playwright test for the file comparison page |

## Installation

Requires Python 3.9 or newer.

```
install -m 755 server.py /usr/local/bin/ant-verify
useradd --system --no-create-home --shell /usr/sbin/nologin ant-verify
install -d -m 750 -o root -g ant-verify /var/lib/ant-verify
cp systemd/ant-verify.service /etc/systemd/system/
systemctl enable --now ant-verify
```

The service listens on `127.0.0.1:8089`. Put the configuration in `nginx/` in front of it.

Records live in `/var/lib/ant-verify/registry.json` and are managed from the command line:

```
ant-verify new
ant-verify add NO --sha256 HEX --size BYTES --subject TEXT --signer NAME --date DD.MM.YYYY [--recipient ORG] [--ref REF] [--replaces OLD_NO]
ant-verify revoke NO [--reason TEXT]
ant-verify list
ant-verify show NO
```

`--subject`, `--recipient`, `--ref` and `--reason` are kept in the record but never shown publicly.

## License

GPL-3.0. The bundled Swagger UI is licensed under Apache-2.0; its text is in `api/ui/LICENSE`.
