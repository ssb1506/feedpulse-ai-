"""
Kafka Config — Provides connection settings that work for both:
  - Local Docker: plain Kafka at kafka:29092
  - Cloud (Aiven): SSL certificate-based authentication

For Aiven cloud deployment, set these env variables:
  KAFKA_BOOTSTRAP_SERVERS=kafka-xxx.aivencloud.com:24851
  KAFKA_SSL=true
  KAFKA_CA_CERT=<base64 encoded ca.pem>
  KAFKA_SERVICE_CERT=<base64 encoded service.cert>
  KAFKA_SERVICE_KEY=<base64 encoded service.key>

For local with cert files, place them in /app/certs/ and set:
  KAFKA_SSL=true
"""

import os
import ssl
import base64
import tempfile


def _write_cert_from_env(env_var: str, filename: str, cert_dir: str) -> str:
    """Decode base64 env var and write to file. Returns file path."""
    b64_content = os.getenv(env_var, "")
    if b64_content:
        content = base64.b64decode(b64_content)
        path = os.path.join(cert_dir, filename)
        with open(path, "wb") as f:
            f.write(content)
        return path
    return ""


def get_ssl_context():
    """Build SSL context from cert files or base64 env vars."""
    cert_dir = os.getenv("KAFKA_CERT_DIR", "/app/certs")
    os.makedirs(cert_dir, exist_ok=True)

    ca_path = os.path.join(cert_dir, "ca.pem")
    cert_path = os.path.join(cert_dir, "service.cert")
    key_path = os.path.join(cert_dir, "service.key")

    # If cert files don't exist, try creating from env vars
    if not os.path.exists(ca_path):
        _write_cert_from_env("KAFKA_CA_CERT", "ca.pem", cert_dir)
    if not os.path.exists(cert_path):
        _write_cert_from_env("KAFKA_SERVICE_CERT", "service.cert", cert_dir)
    if not os.path.exists(key_path):
        _write_cert_from_env("KAFKA_SERVICE_KEY", "service.key", cert_dir)

    if not all(os.path.exists(p) for p in [ca_path, cert_path, key_path]):
        raise FileNotFoundError(
            f"SSL certs not found. Either place files in {cert_dir} "
            f"or set KAFKA_CA_CERT, KAFKA_SERVICE_CERT, KAFKA_SERVICE_KEY env vars."
        )

    context = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=ca_path,
    )
    context.load_cert_chain(
        certfile=cert_path,
        keyfile=key_path,
    )
    context.check_hostname = True
    return context


def get_producer_config() -> dict:
    """Returns kafka-python KafkaProducer kwargs."""
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    use_ssl = os.getenv("KAFKA_SSL", "false").lower() == "true"

    config = {
        "bootstrap_servers": servers,
    }

    if use_ssl:
        config.update({
            "security_protocol": "SSL",
            "ssl_context": get_ssl_context(),
        })

    return config


def get_consumer_config(group_id: str = "feedpulse-consumer") -> dict:
    """Returns kafka-python KafkaConsumer kwargs."""
    config = get_producer_config()
    config.update({
        "auto_offset_reset": "latest",
        "enable_auto_commit": True,
        "group_id": group_id,
        "consumer_timeout_ms": 1000,
    })
    return config
