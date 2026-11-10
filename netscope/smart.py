"""Plain-language, dependency-free connection diagnostics."""
from __future__ import annotations

import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import cli


def diagnose(host: str = "example.com", timeout: float = 3.0, lang: str = "en") -> dict[str, Any]:
    """Run bounded DNS, TCP, HTTPS and optional ping checks for one host."""
    if not 0.5 <= timeout <= 10:
        raise ValueError("timeout must be between 0.5 and 10 seconds")

    if lang not in ("en", "ru", "tg"):
        raise ValueError("lang must be en, ru or tg")

    started = time.perf_counter()
    dns = cli.dns_lookup(host)
    tcp = cli.check_port(host, 443, timeout)
    https: dict[str, Any] = {"checked": True, "ok": False}
    try:
        request = Request("https://" + host + "/", method="HEAD",
                          headers={"User-Agent": "NetScope/0.3.0"})
        with urlopen(request, timeout=timeout) as response:
            https.update({"ok": 200 <= response.status < 500,
                          "status_code": response.status})
    except HTTPError as exc:
        # An HTTP response, even 4xx/5xx, proves DNS/TCP/TLS/HTTP worked.
        https.update({"ok": True, "status_code": exc.code,
                      "note": "The server returned an HTTP error status."})
    except (URLError, OSError, TimeoutError) as exc:
        https["error"] = str(getattr(exc, "reason", exc))[:240]

    ping = cli.ping_host(host, count=3, timeout=max(1, int(timeout)))
    checks = {"dns": dns, "tcp_443": tcp, "https": https, "ping": ping}
    findings: list[dict[str, str]] = []

    messages = {
        "en": {
            "dns_title": "DNS: the hostname could not be resolved",
            "dns_why": "DNS did not return an address for this host.",
            "dns_action": "Check the hostname, try another network, or compare DNS settings.",
            "secure_title": "The secure connection could not be established",
            "secure_why": "DNS worked, but TCP port 443 or the HTTPS request failed.",
            "secure_action": "Check firewall, VPN, captive portal, carrier restrictions, and whether the host is online.",
            "healthy_title": "The secure connection is reachable",
            "healthy_why": "NetScope resolved the host and received a successful HTTPS response or HTTP status.",
            "healthy_action": "If an app still fails, check that app's own server, account, proxy, or configuration.",
            "loss_title": "Packet loss was reported by ping",
            "loss_why": "{loss}% packet loss can cause delays or interruptions.",
            "loss_action": "Repeat the test; compare Wi-Fi/mobile data and move closer to the access point.",
            "ping_title": "Ping was unavailable or blocked",
            "ping_why": "The ping command did not receive replies.",
            "ping_action": "This alone does not mean the internet is down; some networks block ICMP. Use the DNS, TCP and HTTPS results.",
            "latency_title": "Ping latency is high",
            "latency_why": "Average round-trip time was {avg} ms.",
            "latency_action": "Try a closer server, pause large downloads, or compare another network."
        },
        "ru": {
            "dns_title": "DNS: не удалось определить IP-адрес сайта",
            "dns_why": "DNS не вернул IP-адрес для этого имени хоста.",
            "dns_action": "Проверьте адрес сайта, попробуйте другую сеть или сравните настройки DNS.",
            "secure_title": "Не удалось установить защищённое соединение",
            "secure_why": "DNS работает, но подключение к TCP-порту 443 или запрос HTTPS завершились ошибкой.",
            "secure_action": "Проверьте брандмауэр, VPN, страницу авторизации Wi-Fi, ограничения оператора и доступность сайта.",
            "healthy_title": "Защищённое соединение доступно",
            "healthy_why": "NetScope определил адрес сайта и получил ответ HTTPS или HTTP.",
            "healthy_action": "Если приложение всё ещё не работает, проверьте его сервер, учётную запись, прокси и настройки.",
            "loss_title": "Ping обнаружил потерю пакетов",
            "loss_why": "Потеря пакетов {loss}% может вызывать задержки и обрывы.",
            "loss_action": "Повторите проверку, сравните Wi-Fi и мобильную сеть, приблизьтесь к роутеру.",
            "ping_title": "Ping недоступен или заблокирован",
            "ping_why": "Команда ping не получила ответов.",
            "ping_action": "Это не доказывает отсутствие интернета: некоторые сети блокируют ICMP. Ориентируйтесь также на DNS, TCP и HTTPS.",
            "latency_title": "Высокая задержка Ping",
            "latency_why": "Среднее время ответа составило {avg} мс.",
            "latency_action": "Попробуйте ближайший сервер, остановите большие загрузки или сравните другую сеть."
        },
        "tg": {
            "dns_title": "DNS: суроғаи IP-и сомона ёфт нашуд",
            "dns_why": "DNS барои ин номи сомона суроғаи IP барнагардонд.",
            "dns_action": "Номи сомонаро санҷед, шабакаи дигарро истифода баред ё танзимоти DNS-ро муқоиса кунед.",
            "secure_title": "Пайвасти бехатар барқарор нашуд",
            "secure_why": "DNS кор кард, аммо пайвастшавӣ ба TCP-порти 443 ё дархости HTTPS ноком шуд.",
            "secure_action": "Сипар, VPN, саҳифаи воридшавии Wi-Fi, маҳдудияти оператор ва дастрасии сомонаро санҷед.",
            "healthy_title": "Пайвасти бехатар дастрас аст",
            "healthy_why": "NetScope суроғаи сомонаро ёфт ва аз HTTPS ё HTTP ҷавоб гирифт.",
            "healthy_action": "Агар барнома ҳанӯз кор накунад, сервер, ҳисоб, прокси ва танзимоти худи барномаро санҷед.",
            "loss_title": "Ping талафи бастаҳои маълумотро нишон дод",
            "loss_why": "Талафи {loss}% бастаҳо метавонад таъхир ё қатъшавиро ба вуҷуд орад.",
            "loss_action": "Санҷишро такрор кунед, Wi-Fi ва интернети мобилиро муқоиса кунед ва ба роутер наздиктар шавед.",
            "ping_title": "Ping дастнорас аст ё баста шудааст",
            "ping_why": "Фармони ping ҷавоб нагирифт.",
            "ping_action": "Ин танҳо маънои қатъ будани интернетро надорад: баъзе шабакаҳо ICMP-ро мебанданд. Натиҷаҳои DNS, TCP ва HTTPS-ро низ бинед.",
            "latency_title": "Таъхири Ping баланд аст",
            "latency_why": "Вақти миёнаи ҷавоб {avg} мс буд.",
            "latency_action": "Сервери наздиктарро санҷед, боргирии калонро боздоред ё шабакаи дигарро муқоиса кунед."
        }
    }[lang]

    if not dns.get("ok"):
        status = "problem"
        findings.append({
            "title": messages["dns_title"],
            "why": messages["dns_why"],
            "action": messages["dns_action"]
        })
    elif not tcp.get("open") and not https.get("ok"):
        status = "limited"
        findings.append({
            "title": messages["secure_title"],
            "why": messages["secure_why"],
            "action": messages["secure_action"]
        })
    else:
        status = "healthy"
        findings.append({
            "title": messages["healthy_title"],
            "why": messages["healthy_why"],
            "action": messages["healthy_action"]
        })

    if ping.get("ok"):
        stats = ping.get("statistics", {})
        loss = stats.get("packet_loss_percent")
        avg = stats.get("avg_ms")
        if loss is not None and loss > 0:
            findings.append({
                "title": messages["loss_title"],
                "why": messages["loss_why"].format(loss=loss),
                "action": messages["loss_action"]
            })
        if avg is not None and avg > 150:
            findings.append({
                "title": messages["latency_title"],
                "why": messages["latency_why"].format(avg=avg),
                "action": messages["latency_action"]
            })
    else:
        findings.append({
            "title": messages["ping_title"],
            "why": ping.get("error", messages["ping_why"]),
            "action": messages["ping_action"]
        })

    return {
        "tool": "NetScope",
        "version": cli.VERSION,
        "host": host,
        "status": status,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "checks": checks,
        "findings": findings,
        "privacy": "Results are generated locally and are not uploaded by NetScope."
    }
