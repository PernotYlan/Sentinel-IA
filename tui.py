#!/usr/bin/env python3
"""
Sentinel-IA — Interface d'administration
Lance avec : python3 tui.py
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog
from textual.screen import ModalScreen
from textual.containers import Horizontal
from textual.reactive import reactive
from textual import work
from rich.text import Text
from collections import deque
import asyncio
import random
import time
import psutil
from datetime import datetime


class DetachPopup(ModalScreen):
    """Popup explicatif pour le detachement tmux"""

    BINDINGS = [("escape", "dismiss", "Fermer")]

    def compose(self) -> ComposeResult:
        yield Static(
            "\n"
            " [bold]Detachement — tmux[/bold]\n\n"
            " Textual ne supporte pas le detachement natif.\n"
            " Utilise [cyan]tmux[/cyan] pour lancer et detacher le TUI :\n\n"
            "   [green]tmux new -s sentinel[/green]       creer une session\n"
            "   [green]python3 tui.py[/green]             lancer le TUI\n"
            "   [yellow]Ctrl+B  puis  D[/yellow]            detacher\n"
            "   [green]tmux attach -t sentinel[/green]    reattacher\n\n"
            " Installation : [cyan]apt install tmux[/cyan]\n\n"
            " [dim]Appuie sur Echap pour fermer[/dim]\n",
            id="popup_content"
        )

    DEFAULT_CSS = """
    DetachPopup {
        align: center middle;
    }
    #popup_content {
        width: 52;
        height: 18;
        border: solid yellow;
        background: $surface;
        padding: 0 1;
    }
    """


class EnvStatus(Static):
    """Panneau d'etat de l'environnement systeme"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        net = psutil.net_io_counters()
        self._last_bytes_sent = net.bytes_sent
        self._last_bytes_recv = net.bytes_recv
        self._last_time = time.time()
        self._tx_mbps: float = 0.0
        self._rx_mbps: float = 0.0

    def _update_net(self):
        now = time.time()
        net = psutil.net_io_counters()
        elapsed = now - self._last_time or 1
        self._tx_mbps = (net.bytes_sent - self._last_bytes_sent) / elapsed / 1024 / 1024
        self._rx_mbps = (net.bytes_recv - self._last_bytes_recv) / elapsed / 1024 / 1024
        self._last_bytes_sent = net.bytes_sent
        self._last_bytes_recv = net.bytes_recv
        self._last_time = now

    def _bar(self, t: Text, label: str, percent: float, color: str):
        filled = int(percent / 10)
        bar = "█" * filled + "░" * (10 - filled)
        t.append(f"{label:<5}", style="bold")
        t.append(f" [{bar}] ", style=color)
        t.append(f"{percent:>4.0f}%\n")

    def render(self) -> Text:
        self._update_net()
        cpu  = psutil.cpu_percent()
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        t = Text()
        t.append("Env Status\n", style="bold")
        t.append("clientA\n\n", style="cyan bold")
        self._bar(t, "CPU",  cpu,  "red" if cpu  > 80 else "green")
        self._bar(t, "RAM",  ram,  "red" if ram  > 80 else "blue")
        self._bar(t, "Disk", disk, "red" if disk > 80 else "yellow")
        t.append("\n")
        t.append("Net TX  ", style="bold")
        t.append(f"{self._tx_mbps:>6.2f} MB/s\n", style="green")
        t.append("Net RX  ", style="bold")
        t.append(f"{self._rx_mbps:>6.2f} MB/s\n", style="blue")
        return t


class Counters(Static):
    """Panneau de compteurs d'evenements - affiche le debit en ev/min"""

    zeek_rate: reactive[float] = reactive(0.0)
    syslog_rate: reactive[float] = reactive(0.0)
    db_rate: reactive[float] = reactive(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._zeek_ts: deque = deque()
        self._syslog_ts: deque = deque()
        self._db_ts: deque = deque()

    def _rate(self, ts_deque: deque) -> float:
        now = time.time()
        cutoff = now - 60
        while ts_deque and ts_deque[0] < cutoff:
            ts_deque.popleft()
        return float(len(ts_deque))

    def record(self, source: str):
        now = time.time()
        if source == "zeek":
            self._zeek_ts.append(now)
            self.zeek_rate = self._rate(self._zeek_ts)
        elif source == "syslog":
            self._syslog_ts.append(now)
            self.syslog_rate = self._rate(self._syslog_ts)
        elif source == "db":
            self._db_ts.append(now)
            self.db_rate = self._rate(self._db_ts)

    def render(self) -> Text:
        t = Text()
        t.append("Evenements / min\n\n", style="bold")
        t.append("Zeek    ", style="green")
        t.append(f"{self.zeek_rate:>8.1f}\n")
        t.append("Syslog  ", style="blue")
        t.append(f"{self.syslog_rate:>8.1f}\n")
        t.append("Autres  ", style="yellow")
        t.append(f"{self.db_rate:>8.1f}\n")
        return t


class Travailleurs(Static):
    """Panneau d'etat des workers et de leurs files d'attente"""

    w1_queue: reactive[int] = reactive(0)
    w2_queue: reactive[int] = reactive(0)
    w3_queue: reactive[int] = reactive(0)
    w4_queue: reactive[int] = reactive(0)
    anomalies: reactive[int] = reactive(0)

    w1_online: reactive[bool] = reactive(True)
    w2_online: reactive[bool] = reactive(True)
    w3_online: reactive[bool] = reactive(True)
    w4_online: reactive[bool] = reactive(False)

    def _worker_line(self, t: Text, name: str, online: bool, queue: int):
        if online:
            t.append("● ", style="green")
            t.append(f"{name:<12}", style="bold")
            t.append("  queue: ")
            t.append(str(queue), style="cyan")
            t.append("\n")
        else:
            t.append("● ", style="red")
            t.append(f"{name:<12}", style="dim")
            t.append("  offline\n", style="dim")

    def render(self) -> Text:
        anomaly_str = "999+" if self.anomalies >= 1000 else str(self.anomalies)
        t = Text()
        t.append("Travailleurs\n\n", style="bold")
        self._worker_line(t, "Worker 1", self.w1_online, self.w1_queue)
        self._worker_line(t, "Worker 2", self.w2_online, self.w2_queue)
        self._worker_line(t, "Worker 3", self.w3_online, self.w3_queue)
        self._worker_line(t, "Worker 4", self.w4_online, self.w4_queue)
        t.append("\nAnomalies ", style="red bold")
        t.append(anomaly_str, style="red")
        return t


class SentinelTUI(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #top_row {
        height: 12;
    }

    EnvStatus {
        width: 35;
        height: 100%;
        border: solid green;
        padding: 1 2;
    }

    Counters {
        width: 28;
        height: 100%;
        border: solid blue;
        padding: 1 2;
    }

    Travailleurs {
        width: 1fr;
        height: 100%;
        border: solid magenta;
        padding: 1 2;
    }

    #log_panel {
        border: solid yellow;
        padding: 0 1;
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("m", "menu", "Menu"),
        ("d", "detach", "Detacher"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="top_row"):
            yield EnvStatus()
            yield Counters()
            yield Travailleurs()
        yield RichLog(id="log_panel", highlight=True, markup=True)
        yield Footer()

    def action_menu(self):
        pass

    def action_detach(self):
        self.push_screen(DetachPopup())

    def on_mount(self):
        self.title = "Sentinel-IA"
        self.sub_title = "Surveillance reseau en temps reel"
        self.set_interval(2, self.query_one(EnvStatus).refresh)
        self._simulate()

    @work(exclusive=False)
    async def _simulate(self):
        """Simule des evenements entrants pour tester le rendu"""
        log = self.query_one(RichLog)
        counters = self.query_one(Counters)
        workers = self.query_one(Travailleurs)
        sources = ["zeek", "zeek", "zeek", "syslog", "db"]

        while True:
            await asyncio.sleep(0.3)
            source = random.choice(sources)
            ts = datetime.now().strftime("%H:%M:%S")

            if source == "zeek":
                counters.record("zeek")
                workers.w1_queue = max(0, workers.w1_queue + random.randint(-1, 2))
                log.write(f"[green]{ts}[/green]  [bold]ZEEK[/bold]    192.168.1.{random.randint(1,254)} → 10.0.0.{random.randint(1,10)}  port {random.randint(1024,65535)}")
                if random.random() < 0.05:
                    workers.anomalies += 1
                    workers.w2_queue = max(0, workers.w2_queue + 1)
                    workers.w3_queue = max(0, workers.w3_queue + 1)
                    log.write(f"[red]{ts}[/red]  [bold red]ANOMALIE[/bold red] IF → XGB → AE  src=192.168.1.{random.randint(1,254)}")
            elif source == "syslog":
                counters.record("syslog")
                log.write(f"[blue]{ts}[/blue]  [bold]SYSLOG[/bold]  auth: session opened for user root")
            else:
                counters.record("db")
                log.write(f"[yellow]{ts}[/yellow]  [bold]AUTRE[/bold]   tags inconnus, dumpe dans SQLite")

            workers.w2_queue = max(0, workers.w2_queue - 1)
            workers.w3_queue = max(0, workers.w3_queue - 1)


if __name__ == "__main__":
    SentinelTUI().run()
